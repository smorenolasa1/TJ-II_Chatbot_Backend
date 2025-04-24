import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend for compatibility
import matplotlib.pyplot as plt
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import requests
import re
import json

# Load environment variables
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

# Configure Gemini AI
genai.configure(api_key=google_api_key)
MODEL_NAME = "models/gemini-1.5-pro"

# FastAPI setup
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory for storing plots
PLOT_DIR = "static"
os.makedirs(PLOT_DIR, exist_ok=True)

# Function to fetch similar signals
# Function to fetch similar signals
def get_similar_signals(shot_number, database_name, tIni=None, tFin=None):  # ✅ Accepts database_name as a parameter
    if tIni and tFin:
        # Use Servlet4 when tIni and tFin are provided
        server_url_similar = "http://localhost:8080/Servlet4"
        params_similar = {
            "dbDirectory": "primitive_DB",
            "dbName": database_name,
            "signalName": database_name,
            "shotNumber": shot_number,
            "tIni": tIni,
            "tFin": tFin,
            "match": "32"
        }
    else:
        # Default to Servlet6 when no specific time window is provided
        server_url_similar = "http://localhost:8080/Servlet6"
        params_similar = {
            "dbDirectory": "primitive_DB",
            "dbName": "TESTING",  # if needed, replace this with database_name
            "signalName": database_name,
            "shotNumber": shot_number,
            "tIni": "0.0",
            "tFin": "0.0",
            "match": "32"
        }

    print(f"📡 Fetching similar signals for shot: {shot_number} from database: {database_name}")

    try:
        response_similar = requests.get(server_url_similar, params=params_similar)
        print(f"✅ Raw Response from Servlet6:\n{response_similar.text[:500]}")  # Debugging

        if not response_similar.ok:
            print(f"❌ Error: Servlet6 returned status {response_similar.status_code}")
            return []

        response_text = response_similar.text.strip().split("\n")

        # Ensure valid response format
        if len(response_text) < 3 or not response_text[2]:
            print("❌ Error: Unexpected response format from Servlet6.")
            return []

        # Extract confidence scores and shot numbers
        try:
            if "Servlet4" in server_url_similar:
                # Parsing format for Servlet4: shot, tIni, duration, confidence
                filtered_lines = [
                    line.strip() for line in response_text[2:] if len(line.split()) >= 4
                ]
                similar_shots = []
                for line in filtered_lines[:4]:
                    parts = line.split()
                    shot = parts[0]
                    tIni_val = float(parts[1].replace(",", "."))
                    duration = float(parts[2].replace(",", "."))
                    confidence = float(parts[3].replace(",", "."))
                    similar_shots.append((confidence, shot))  # Only return what's needed
            else:
                # Parsing format for Servlet6: confidence, shot
                filtered_lines = [
                    line.strip() for line in response_text[2:] if len(line.split()) >= 2
                ]
                similar_shots = [
                    (float(line.split()[0].replace(",", ".")), line.split()[1])
                    for line in filtered_lines
                ]

            print(f"✅ Parsed Similar Shots: {similar_shots}")
            print(f"📡 Request to Servlet6: {server_url_similar} with params {params_similar}")
            return similar_shots[:4]  # Return top 4 similar shots

        except ValueError as e:
            print(f"❌ Error parsing response: {e}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to Servlet6: {e}")
        return []

# Function to fetch and plot signals
def plot_signals(shot_number, similar_shots, signal_name):
    server_url_signal = "http://localhost:8080/Servlet7"
    similar_only = [shot[1] for shot in similar_shots if shot[1] != shot_number]
    all_shots = [shot_number] + similar_only
    plt.figure(figsize=(10, 5))

    print(f"📡 Generating plot for signal: {signal_name}")
    for shot in all_shots:
        params_signal = {
            "dbDirectory": "primitive_DB",  
            "dbName": signal_name,          # ✅ Debe ser el nombre correcto de la base de datos
            "signalName": signal_name,      # ✅ Debe ser el nombre correcto de la base de datos
            "shotNumber": shot
        }

        print(f"📡 Request to Servlet7: {server_url_signal} with params {params_signal}")  # ✅ DEBUG PRINT

        response_signal = requests.get(server_url_signal, params=params_signal)

        if response_signal.status_code == 200:
            response_text = response_signal.text.strip()
            print(f"🌟 Response from Servlet7 for shot {shot}: {response_text[:200]}")  # Display first 200 characters
            lines = response_text.split("\n")
            times, amplitudes = [], []
            for line in lines:
                parts = line.split(",")
                if len(parts) == 2:
                    t, amp = float(parts[0]), float(parts[1])
                    times.append(t)
                    amplitudes.append(amp)

            if len(amplitudes) > 0:
                plt.plot(times, amplitudes, label=f"Shot {shot}", linewidth=0.5)

    plt.xlabel("Time")
    plt.ylabel("Amplitude")
    plt.title(f"Signal {signal_name} and Similar Signals")
    plt.legend()

    # 🔑 Ahora incluye tanto la base de datos como el número de descarga en el nombre del archivo
    plot_filename = f"plot_{signal_name}_{shot_number}.png"
    plot_path = os.path.join(PLOT_DIR, plot_filename)
    plt.savefig(plot_path, dpi=300)
    plt.close()

    return plot_path

def clean_ai_response(text):
    """Removes markdown formatting like **bold**, *italic*, and converts it to plain text."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # Remove bold
    text = re.sub(r"\*(.*?)\*", r"\1", text)  # Remove italics
    text = re.sub(r"\n\s*\n", "\n", text)  # Remove extra newlines
    return text.strip()

@app.post("/ask_gemini")
async def ask_gemini(request: Request):
    try:
        data = await request.json()
        print(f"🔍 Incoming Data: {data}")
        # Convert shot_number to a string before using .strip()
        shot_number = str(data.get("shot_number", "")).strip()
        question = str(data.get("question", "")).strip()
        database_name = str(data.get("database_name", "")).strip()
        tIni = str(data.get("tIni", "")).strip()
        tFin = str(data.get("tFin", "")).strip()
        if not shot_number or not question or not database_name:
            raise HTTPException(status_code=400, detail="Missing required data")

        print(f"🔹 Extracted shot_number: {shot_number}, question: {question}, database_name: {database_name}")

        # ✅ Fetch similar signals
        similar_shots = get_similar_signals(shot_number, database_name, tIni, tFin)
        if not similar_shots:
            raise HTTPException(status_code=400, detail="No similar signals found.")

        print(f"✅ Similar shots retrieved: {similar_shots}")

        # ✅ Convert similarity data to text format
        similarity_data = "\n".join([f"Shot {shot}: Confidence {conf:.4f}" for conf, shot in similar_shots])

        # ✅ Ask Gemini AI
        prompt = f"""
        The user is analyzing plasma fusion shot similarities.
        The reference shot number is {shot_number}, and here are the most similar signals:

        {similarity_data}

        The user asks: "{question}"

        Answer clearly in plain text format without using asterisks, markdown, or extra formatting.
        Use bullet points when listing similarities and the confidence level.
        """

        print(f"📡 Sending prompt to Gemini: {prompt[:200]}...")

        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)

        cleaned_response = clean_ai_response(response.text)

        print(f"✅ Cleaned AI Response:\n{cleaned_response}")
        signal_name = database_name
        # ✅ Generate Plot
        plot_path = plot_signals(shot_number, similar_shots, signal_name)
        plot_url = f"http://localhost:5004/static/{os.path.basename(plot_path)}"

        return JSONResponse(content={
            "response": cleaned_response,
            "plot_url": plot_url
        })

    except Exception as e:
        print(f"❌ ERROR in /ask_gemini: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
    
        
@app.post("/extract_shot_number_and_database")
async def extract_shot_number_and_database(request: Request):
    try:
        data = await request.json()
        user_query = data.get("user_query", "").strip()

        if not user_query:
            raise HTTPException(status_code=400, detail="Missing user query")

        print(f"📡 Extracting shot number and database name from query: {user_query}")

        # ✅ Improved Prompt
        prompt = f"""
        The user provided the following query related to plasma fusion shots:
        "{user_query}"
        
        Identify the shot number and the database name they are referring to.
        Possible database names are: "HALFAC4" and "Densidad2_".
        You should also return the initial value and final value. 
        Return the result as a valid JSON object like this:

        {{
            "shot_number": "<shot_number>",
            "database_name": "<database_name>"
            "tIni": "<tIni>",
            "tFin": "<tFin>"
        }}

        If no valid shot number, database name or tIni, tFin is found, return:

        {{
            "shot_number": null,
            "database_name": null
            "tIni": "0.0",
            "tFin": "0.0"
        }}

        Ensure the output is strictly JSON formatted and nothing else.
        """

        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)

        # ✅ Log the raw response before parsing
        raw_response = response.text.strip()
        print(f"🌟 Raw Response from Gemini: {raw_response}")

        # ✅ Remove markdown formatting (triple backticks)
        cleaned_response = re.sub(r"```json\n|```", "", raw_response).strip()
        print(f"✅ Cleaned Response: {cleaned_response}")

        # ✅ Parse the cleaned response as JSON
        try:
            extracted_data = json.loads(cleaned_response)
            shot_number = extracted_data.get("shot_number")
            database_name = extracted_data.get("database_name")

            print(f"✅ Extracted Shot Number: {shot_number}")
            print(f"✅ Extracted Database Name: {database_name}")

            if not shot_number or not database_name:
                return JSONResponse(content={"error": "Shot number or database name not found"}, status_code=200)

            return JSONResponse(content={"shot_number": shot_number, "database_name": database_name})

        except json.JSONDecodeError as e:
            print(f"❌ Error parsing Gemini response: {str(e)}")
            return JSONResponse(content={"error": "Failed to parse Gemini response"}, status_code=500)

    except Exception as e:
        print(f"❌ ERROR in /extract_shot_number_and_database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
    
@app.get("/static/{filename}")
async def serve_plot(filename: str):
    file_path = os.path.join(PLOT_DIR, filename)
    return FileResponse(file_path, media_type="image/png")