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
from datetime import datetime

CONTEXT_DIR = "context"
os.makedirs(CONTEXT_DIR, exist_ok=True)

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

def save_similpattern_context(question, plot_path=None, pattern_summary=None, similar_shots=None):
    context_file = os.path.join(CONTEXT_DIR, "similpattern_history.json")

    if pattern_summary:
        summary = pattern_summary
    elif similar_shots and len(similar_shots[0]) == 2:
        # Format fallback summary from Servlet6
        summary = "\n".join([
            f"{conf:.4f}".replace(".", ",") + f" - {shot}"
            for conf, shot in similar_shots
        ])
    else:
        summary = None

    new_entry = {
        "question": question,
        "plot_path": plot_path,
        "pattern_summary": summary
    }

    try:
        if os.path.exists(context_file):
            with open(context_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = []

        history.append(new_entry)

        with open(context_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

        print(f"✅ Context updated in {context_file}")

    except Exception as e:
        print(f"❌ Error saving context: {e}")
        
# Function to fetch similar signals
def get_similar_signals(shot_number, database_name, tIni=None, tFin=None):
    use_servlet4 = tIni not in ["", "0.0", None] and tFin not in ["", "0.0", None]

    if use_servlet4:
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
        server_url_similar = "http://localhost:8080/Servlet6"
        params_similar = {
            "dbDirectory": "primitive_DB",
            "dbName": "TESTING",  # Cambia si quieres usar database_name
            "signalName": database_name,
            "shotNumber": shot_number,
            "tIni": "0.0",
            "tFin": "0.0",
            "match": "32"
        }

    print(f"📡 Fetching similar signals for shot: {shot_number} from database: {database_name}")

    try:
        response_similar = requests.get(server_url_similar, params=params_similar)
        print(f"✅ Raw Response from backend:\n{response_similar.text[:500]}")

        if not response_similar.ok:
            print(f"❌ Error: backend returned status {response_similar.status_code}")
            return []

        response_text = response_similar.text.strip().split("\n")
        if len(response_text) < 3 or not response_text[2]:
            print("❌ Error: Unexpected response format.")
            return []

        # Parse response depending on the servlet
        similar_shots = []

        if use_servlet4:
            filtered_lines = [line.strip() for line in response_text[2:] if len(line.split()) >= 4]
            for line in filtered_lines[:4]:
                parts = line.split()
                shot = parts[0]
                tIni_val = float(parts[1].replace(",", "."))
                duration = float(parts[2].replace(",", "."))
                confidence = float(parts[3].replace(",", "."))
                tFin_val = tIni_val + duration
                similar_shots.append((confidence, shot, tIni_val, tFin_val))
        else:
            filtered_lines = [line.strip() for line in response_text[2:] if len(line.split()) >= 2]
            similar_shots = [
                (float(line.split()[0].replace(",", ".")), line.split()[1])
                for line in filtered_lines[:4]
            ]

        print(f"✅ Parsed Similar Shots: {similar_shots}")
        print(f"📡 Request to {'Servlet4' if use_servlet4 else 'Servlet6'}: {server_url_similar} with params {params_similar}")

        return similar_shots

    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to servlet: {e}")
        return []
    
# Function to fetch and plot signals (adapted to use tIni/tFin ranges if available)
def plot_signals(shot_number, similar_shots, signal_name, pattern_ranges=None):
    server_url_signal = "http://localhost:8080/Servlet7"
    # Create a list of all shots to plot (reference + similar)
    similar_only = [shot[1] for shot in similar_shots if shot[1] != shot_number]
    all_shots = [shot_number] + similar_only
    plt.figure(figsize=(10, 5))

    # Set up the plot
    print(f"📡 Generating plot for signal: {signal_name}")
    for shot in all_shots:
        # Prepare request parameters to be sent for Servlet7
        params_signal = {
            "dbDirectory": "primitive_DB",  
            "dbName": signal_name,
            "signalName": signal_name,
            "shotNumber": shot
        }
        
        print(f"📡 Request to Servlet7: {server_url_signal} with params {params_signal}")

        # Fetch the signal data from Servlet7
        response_signal = requests.get(server_url_signal, params=params_signal)

        if response_signal.status_code == 200:
            response_text = response_signal.text.strip()
            print(f"🌟 Response from Servlet7 for shot {shot}: {response_text[:200]}")
            lines = response_text.split("\n")
            times, amplitudes = [], []
            
            # Parse signal data into time and amplitude lists
            for line in lines:
                parts = line.split(",")
                if len(parts) == 2:
                    try:
                        t, amp = float(parts[0]), float(parts[1])
                        times.append(t)
                        amplitudes.append(amp)
                    except ValueError:
                        continue

            # If time ranges are specified (from Servlet4), filter the signal data
            if pattern_ranges and shot in pattern_ranges:
                t_min, t_max = pattern_ranges[shot]
                filtered_points = [(t, a) for t, a in zip(times, amplitudes) if t_min <= t <= t_max]
                if filtered_points:
                    times, amplitudes = zip(*filtered_points)
                else:
                    continue  # Skip this shot if no data in range

            # Plot the signal
            if len(amplitudes) > 0:
                plt.plot(times, amplitudes, label=f"Shot {shot}", linewidth=0.5)

    plt.xlabel("Time")
    plt.ylabel("Amplitude")
    plt.title(f"Signal {signal_name} and Similar Signals")
    plt.legend()

    # Create unique filename to avoid caching
    import uuid
    unique_id = uuid.uuid4().hex[:6]
    plot_filename = f"plot_{signal_name}_{shot_number}_{unique_id}.png"
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

        # Extracción de datos
        shot_number = str(data.get("shot_number", "")).strip()
        question = str(data.get("question", "")).strip()
        database_name = str(data.get("database_name", "")).strip()
        tIni = str(data.get("tIni", "")).strip()
        tFin = str(data.get("tFin", "")).strip()

        if not shot_number or not question or not database_name:
            raise HTTPException(status_code=400, detail="Missing required data")

        print(f"🔹 Extracted shot_number: {shot_number}, question: {question}, database_name: {database_name}")

        # Obtener señales similares
        similar_shots = get_similar_signals(shot_number, database_name, tIni, tFin)
        if not similar_shots:
            raise HTTPException(status_code=400, detail="No similar signals found.")

        print(f"✅ Similar shots retrieved: {similar_shots}")

        # Crear resumen tipo: 1,0000 - 56900 - [1020,018 , 1025,3019966]
        pattern_summary = ""
        if len(similar_shots[0]) == 4:  # Solo si incluye tIni y tFin (Servlet4)
            pattern_summary = "\n".join([
                f"{conf:.4f}".replace(".", ",") +
                f" - {shot} - [{str(tini).replace('.', ',')} , {str(tfin).replace('.', ',')}]"
                for conf, shot, tini, tfin in similar_shots
            ])
            print("📊 Pattern Summary:\n" + pattern_summary)

        # Preparar data para Gemini
        if len(similar_shots[0]) == 4:
            similarity_data = "\n".join([
                f"Shot {shot}: Confidence {conf:.4f}"
                for conf, shot, _, _ in similar_shots
            ])
        else:
            similarity_data = "\n".join([
                f"Shot {shot}: Confidence {conf:.4f}"
                for conf, shot in similar_shots
            ])

        prompt = f"""
        You are assisting a plasma fusion researcher in analyzing signal similarity patterns.

        The reference discharge is: {shot_number}  
        The user asked the following question:
        "{question}"

        If no pattern interval is given, just use the confidence and shot number provided. 
        
        Else, present the information in this format. Take into account the tIni and tFin
        values may vary from the user input but they´re still correct:

        1,0000 - 56900 - [1020,018 , 1030,586054]

        Answer clearly in plain text format without using asterisks, markdown, or extra formatting.
        Use bullet points when listing similarities and the confidence level.

        Here is the data to include:
        {pattern_summary or similarity_data}
        """

        print(f"📡 Sending prompt to Gemini: {prompt[:200]}...")

        # Llamada a Gemini
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        cleaned_response = clean_ai_response(response.text)

        print(f"✅ Cleaned AI Response:\n{cleaned_response}")

        # Generar gráfico
        signal_name = database_name
        plot_path = plot_signals(shot_number, similar_shots, signal_name)
        plot_url = f"http://localhost:5004/static/{os.path.basename(plot_path)}"

        # Guardar contexto
        save_similpattern_context(
            question=question,
            plot_path=plot_path,
            pattern_summary=pattern_summary,
            similar_shots=similar_shots
        )

        return JSONResponse(content={
            "response": cleaned_response,
            "plot_url": plot_url,
            "pattern_summary": pattern_summary
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

        prompt = f"""
        The user provided the following query related to plasma fusion shots:
        "{user_query}"
        
        Identify the shot number and the database name they are referring to.
        Possible database names are: "HALFAC4" and "Densidad2_".
        You should also return the initial value and final value. 
        Return the result as a valid JSON object like this:

        {{
            "shot_number": "56918",
            "database_name": "HALFAC4",
            "tIni": "0.0",
            "tFin": "2000.0",
            "signals": ["HALFAC4"]
        }}

        If no valid shot number, database name or tIni, tFin is found, return:

        {{
            "shot_number": null,
            "database_name": null
            "tIni": "0.0",
            "tFin": "0.0"
        }}

        Please ensure the database_name is either "HALFAC4" or "Densidad2_".
        Ensure the output is strictly JSON formatted and nothing else.
        """

        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)

        # Log the raw response before parsing
        raw_response = response.text.strip()
        print(f"🌟 Raw Response from Gemini: {raw_response}")

        # Remove markdown formatting (triple backticks)
        cleaned_response = re.sub(r"```json\n|```", "", raw_response).strip()
        print(f"✅ Cleaned Response: {cleaned_response}")

        # Parse the cleaned response as JSON
        try:
            extracted_data = json.loads(cleaned_response)
            shot_number = extracted_data.get("shot_number")
            database_name = extracted_data.get("database_name")

            print(f"✅ Extracted Shot Number: {shot_number}")
            print(f"✅ Extracted Database Name: {database_name}")

            if not shot_number or not database_name:
                return JSONResponse(content={"error": "Shot number or database name not found"}, status_code=200)

            return JSONResponse(content={
                "shot_number": shot_number,
                "database_name": database_name,
                "tIni": extracted_data.get("tIni", "0.0"),
                "tFin": extracted_data.get("tFin", "0.0")
            })

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