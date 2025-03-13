import matplotlib
matplotlib.use('Agg')  # ✅ Use non-GUI backend to prevent macOS errors

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import matplotlib.pyplot as plt
import numpy as np
import os

app = Flask(__name__)
CORS(app)  # ✅ Allow frontend to make API requests

# Directory to store plots
PLOT_DIR = "static"
os.makedirs(PLOT_DIR, exist_ok=True)

@app.route("/get_similar_signals", methods=["POST"])
def get_similar_signals():
    data = request.json
    shot_number = data.get("shot_number")

    if not shot_number:
        return jsonify({"error": "Missing shot_number"}), 400

    signal_name = "Densidad2_"
    print(f"📡 Processing shot number: {shot_number}")

    # 🔹 Step 1: Get Similar Signals
    server_url_similar = "http://localhost:8080/Servlet6"
    params_similar = {
        "dbDirectory": "primitive_DB",
        "dbName": "Densidad2_",
        "signalName": signal_name,
        "shotNumber": shot_number,
        "tIni": "0.0",
        "tFin": "0.0",
        "match": "32"
    }

    response_similar = requests.get(server_url_similar, params=params_similar)
    response_text = response_similar.text.strip().split("\n")

    # 🔹 Extract confidence & shot numbers
    filtered_lines = [line.strip() for line in response_text[2:] if len(line.split()) >= 2]
    similar_shots = [(float(line.split()[0].replace(",", ".")), line.split()[1]) for line in filtered_lines]

    # 🔹 Take top 5 similar signals
    top_similar_shots = similar_shots[:4]
    all_shots = [shot_number] + [shot[1] for shot in top_similar_shots]

    # 🔹 Step 2: Fetch and Plot Signals
    server_url_signal = "http://localhost:8080/Servlet7"
    
    plt.figure(figsize=(10, 5))

    for shot in all_shots:
        params_signal = {"signalName": signal_name, "shotNumber": shot}
        response_signal = requests.get(server_url_signal, params=params_signal)

        if response_signal.status_code == 200:
            response_text = response_signal.text.strip()
            try:
                lines = response_text.split("\n")
                times, amplitudes = [], []
                for line in lines:
                    parts = line.split(",")
                    if len(parts) == 2:
                        t, amp = float(parts[0]), float(parts[1])
                        times.append(t)
                        amplitudes.append(amp)

                print(f"📊 Shot {shot} - Time Samples: {len(times)}, Amplitude Samples: {len(amplitudes)}")

                times = np.array(times)
                amplitudes = np.array(amplitudes)

                if len(amplitudes) == 0:
                    print(f"⚠️ No amplitude data for shot {shot}, skipping plot.")
                    continue

                plt.plot(times, amplitudes, label=f"Shot {shot}", linewidth=0.5)

            except ValueError:
                print(f"❌ Error processing shot {shot} data")
                continue

    plt.xlabel("Time")
    plt.ylabel("Amplitude")
    plt.title(f"Signal {signal_name} and 4 Most Similar Signals")
    plt.legend()

    # 🔹 Step 3: Save the plot
    plot_filename = f"plot_{shot_number}.png"
    plot_path = os.path.join(PLOT_DIR, plot_filename)
    plt.savefig(plot_path, dpi=300)
    plt.close()

    # 🔹 Return similar signals + plot URL
    plot_url = f"http://localhost:5000/static/{plot_filename}"

    return jsonify({
        "similar_signals": [{"shot": shot, "confidence": conf} for conf, shot in top_similar_shots],
        "plot_url": plot_url
    })

# 🔹 Serve static plot images
@app.route("/static/<filename>")
def serve_plot(filename):
    return send_file(os.path.join(PLOT_DIR, filename), mimetype="image/png")

if __name__ == "__main__":
    app.run(debug=True, port=5000)