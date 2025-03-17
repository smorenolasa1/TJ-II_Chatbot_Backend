import os
import json
import re
import requests
import matplotlib.pyplot as plt
from io import BytesIO
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from langchain_community.llms import Replicate
import matplotlib
matplotlib.use('Agg')  # ✅ Prevents GUI errors in Flask

import matplotlib.pyplot as plt
# Load environment variables
load_dotenv()
os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")

# Initialize Flask
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Set up Replicate LLaMA-2
llm = Replicate(
    model="meta/meta-llama-3-8b-instruct",
    model_kwargs={"temperature": 0.1, "max_new_tokens": 100}
)

BASE_URL = "https://info.fusion.ciemat.es/cgi-bin/TJII_data.cgi"


def parse_user_input_with_ai(user_input):
    """Uses an AI model to extract structured data from user input."""
    prompt = f"""
    You are an AI that extracts structured data from user requests for plasma diagnostics.
    The user will provide a request in natural language, and you must extract the following fields:

    - "shot": integer (discharge number)
    - "tstart": float (start time in seconds, if provided, otherwise 0.00)
    - "tstop": float (stop time in seconds, if provided, otherwise 2000.00)
    - "signals": list of signal names (always as an array, even if only one signal is given)

    The input can be structured in different ways. Here are some examples of valid inputs and the expected structured output:

    **Example 1:**
    Input: "Give me the diagram for signals TFI of shot 57546"
    Output: {{"shot": 57546, "tstart": null, "tstop": null, "signals": ["TFI"]}}

    **Example 2:**
    Input: "Plot TFI and Densidad2_ for shot 57547 from 0 to 2000"
    Output: {{"shot": 57547, "tstart": 0, "tstop": 2000, "signals": ["TFI", "Densidad2_"]}}

    Now, extract structured data from the following input:
    "{user_input}"

    Provide ONLY the response in a valid JSON format. Do NOT include any extra text, explanations, or greetings.
    """

    response = llm.invoke(prompt).strip()
    print("🤖 AI Response:", response)

    try:
        parsed_data = json.loads(response)  # Convert response to JSON
        return parsed_data
    except json.JSONDecodeError:
        return None


def generate_url(shot, nsignal, signals, factors, tstart, tstop):
    """Generates a URL to fetch signal data."""
    tstart = 0 if tstart is None else tstart
    tstop = 2000 if tstop is None else tstop

    url = f"{BASE_URL}?shot={shot}&nsignal={nsignal}"
    for i in range(1, nsignal + 1):
        signal = signals[i - 1] if i - 1 < len(signals) else ""
        factor = factors[i - 1] if i - 1 < len(factors) else "1.00"
        url += f"&signal{i:02}={signal}&fact{i:02}={factor}"
    
    url += f"&tstart={tstart:.2f}&tstop={tstop:.2f}"
    
    return url


def fetch_data(url):
    """Fetches data from TJ-II URL."""
    response = requests.get(url, verify=False)
    return response.text if response.status_code == 200 else None


def extract_data_points(html_content, signals):
    """Extracts signal data from HTML content."""
    data_points_dict = {}
    matches = list(re.finditer(r"var data(\d{2}) = \[(.*?)\];", html_content, re.DOTALL))
    
    for signal_name in signals:
        match = next((m for m in matches if f"var data{signals.index(signal_name)+1:02}" in m.group(0)), None)
        if match:
            data_block = match.group(2)
            data_points = [tuple(map(float, line.strip('[]').split(','))) for line in data_block.split('],[')]
            data_points_dict[signal_name] = data_points
    
    return data_points_dict


def plot_data(data_points_dict):
    """Creates a plot from signal data and returns an image buffer."""
    fig, ax = plt.subplots(figsize=(10, 6))

    for signal_name, data_points in data_points_dict.items():
        if not data_points:
            print(f"⚠️ No data for signal {signal_name}, skipping plot.")
            continue
        x_values, y_values = zip(*data_points)
        ax.plot(x_values, y_values, label=signal_name, linewidth=1.5)

    ax.set_title("TJ-II Plasma Signals")
    ax.set_xlabel("Time")
    ax.set_ylabel("Value")
    ax.legend()
    ax.grid()

    img_buffer = BytesIO()
    plt.savefig(img_buffer, format="png")  # ✅ Save to buffer (no GUI needed)
    img_buffer.seek(0)
    plt.close(fig)  # ✅ Close figure to prevent memory leaks

    return img_buffer


@app.route("/get_tjii_plot", methods=["POST"])
def get_tjii_plot():
    """API endpoint to process TJ-II data request and return a plotted image."""
    try:
        # Debug: Print incoming request
        data = request.json
        print("📥 Incoming Request Data:", data)

        if not data or "user_query" not in data:
            print("❌ Error: Missing 'user_query' in request")
            return jsonify({"error": "Invalid request format"}), 400

        # AI parses input correctly
        user_input = data["user_query"]
        parsed_data = parse_user_input_with_ai(user_input)
        print("🤖 Parsed Data:", parsed_data)

        if not parsed_data or "shot" not in parsed_data:
            print("❌ Error: AI did not return a shot number")
            return jsonify({"error": "AI parsing failed"}), 400

        # Extract shot number and signals
        shot = parsed_data["shot"]
        signals = parsed_data.get("signals", ["Densidad2_"])
        tstart = parsed_data.get("tstart", 0)
        tstop = parsed_data.get("tstop", 2000)

        print(f"🔹 Fetching data for Shot: {shot}, Signals: {signals}")

        # Generate URL and fetch data
        url = generate_url(shot, len(signals), signals, ["1.00"] * len(signals), tstart, tstop)  # ✅ Corrected
        print(f"🌍 Generated URL: {url}")

        html_content = fetch_data(url)
        if not html_content:
            print("❌ Error: Failed to fetch data from TJ-II")
            return jsonify({"error": "Failed to fetch data"}), 500

        # Extract data
        data_points_dict = extract_data_points(html_content, signals)
        if not data_points_dict:
            print("❌ Error: No data extracted from HTML response")
            return jsonify({"error": "No signal data found"}), 500

        # Plot data
        img_buffer = plot_data(data_points_dict)
        print("📊 Successfully generated plot")
        return send_file(img_buffer, mimetype="image/png")

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)