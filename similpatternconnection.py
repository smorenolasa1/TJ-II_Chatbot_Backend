import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend for compatibility
import matplotlib.pyplot as plt
import google.generativeai as genai
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")

# Configure Gemini AI
genai.configure(api_key=google_api_key)
MODEL_NAME = "models/gemini-1.5-pro"

# Flask setup
app = Flask(__name__)
CORS(app)

# Directory for storing plots
PLOT_DIR = "static"
os.makedirs(PLOT_DIR, exist_ok=True)

# Function to fetch similar signals
def get_similar_signals(shot_number):
    server_url_similar = "http://localhost:8080/Servlet6"

    # ✅ Restore original request format
    params_similar = {
        "dbDirectory": "primitive_DB",
        "dbName": "Densidad2_",
        "signalName": "Densidad2_",  # Ensure correct signal name
        "shotNumber": shot_number,
        "tIni": "0.0",
        "tFin": "0.0",
        "match": "32"
    }

    print(f"📡 Fetching similar signals for shot: {shot_number}")

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
            filtered_lines = [
                line.strip() for line in response_text[2:] if len(line.split()) >= 2
            ]
            similar_shots = [
                (float(line.split()[0].replace(",", ".")), line.split()[1])
                for line in filtered_lines
            ]

            print(f"✅ Parsed Similar Shots: {similar_shots}")
            return similar_shots[:4]  # Return top 4 similar shots

        except ValueError as e:
            print(f"❌ Error parsing response: {e}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to Servlet6: {e}")
        return []
    
# Function to fetch and plot signals
def plot_signals(shot_number, similar_shots):
    server_url_signal = "http://localhost:8080/Servlet7"
    signal_name = "Densidad2_"
    all_shots = [shot_number] + [shot[1] for shot in similar_shots]

    plt.figure(figsize=(10, 5))

    for shot in all_shots:
        params_signal = {"signalName": signal_name, "shotNumber": shot}
        response_signal = requests.get(server_url_signal, params=params_signal)

        if response_signal.status_code == 200:
            response_text = response_signal.text.strip()
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

    plot_filename = f"plot_{shot_number}.png"
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

@app.route("/ask_gemini", methods=["POST"])
def ask_gemini():
    try:
        data = request.get_json()
        shot_number = data.get("shot_number", "").strip()
        question = data.get("question", "").strip()

        if not shot_number:
            return jsonify({"error": "Missing shot_number"}), 400

        if not question:
            return jsonify({"error": "Missing question"}), 400

        print(f"🔹 Extracted shot_number: {shot_number}, question: {question}")

        # ✅ Fetch similar signals
        similar_shots = get_similar_signals(shot_number)
        if not similar_shots:
            return jsonify({"error": "No similar signals found."}), 400

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

        # ✅ Generate Plot
        plot_path = plot_signals(shot_number, similar_shots)
        plot_url = f"http://localhost:5000/static/{os.path.basename(plot_path)}"

        return jsonify({
            "response": cleaned_response,
            "plot_url": plot_url
        })

    except Exception as e:
        print(f"❌ ERROR in /ask_gemini: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500   

@app.route("/extract_shot_number", methods=["POST"])
def extract_shot_number():
    try:
        data = request.get_json()
        user_query = data.get("user_query", "").strip()

        if not user_query:
            return jsonify({"error": "Missing user query"}), 400

        print(f"📡 Extracting shot number from query: {user_query}")

        # ✅ Use Gemini AI to extract the correct shot number
        prompt = f"""
        The user provided the following query related to plasma fusion shots:
        "{user_query}"
        
        Identify the shot number they are referring to.
        If multiple numbers exist, pick the most relevant one.
        If no shot number is found, return "None".
        Return ONLY the shot number without any additional text.
        
        """

        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)

        extracted_shot_number = response.text.strip()

        print(f"✅ Extracted Shot Number: {extracted_shot_number}")

        if not extracted_shot_number.isdigit():
            return jsonify({"shot_number": None, "message": "No valid shot number found."}), 200

        return jsonify({"shot_number": extracted_shot_number})

    except Exception as e:
        print(f"❌ ERROR in /extract_shot_number: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/static/<filename>")
def serve_plot(filename):
    return send_file(os.path.join(PLOT_DIR, filename), mimetype="image/png")

if __name__ == "__main__":
    app.run(debug=True, port=5000)