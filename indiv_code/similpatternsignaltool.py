import requests
import matplotlib.pyplot as plt
import numpy as np

# User input
signal_name = "Densidad2_"
shot_number = "56964"

# Endpoint to get similar signals
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

# Get response from the server
response_similar = requests.get(server_url_similar, params=params_similar)
response_text = response_similar.text.strip().split("\n")

# Filter and extract confidence & shot numbers
filtered_lines = [line.strip() for line in response_text[2:] if len(line.split()) >= 2]
similar_shots = [(float(line.split()[0].replace(",", ".")), line.split()[1]) for line in filtered_lines]

# Take only the **top 5 similar signals**
top_similar_shots = similar_shots[:4]

# ✅ **Print only the confidence scores as requested**
for confidence, shot in top_similar_shots:
    print(f"   - Shot {shot}: Confidence {confidence:.4f}")

# Endpoint to fetch the signal data
server_url_signal = "http://localhost:8080/Servlet7"

# List of all shots to plot (original + 5 similar ones)
all_shots = [shot_number] + [shot[1] for shot in top_similar_shots]

plt.figure(figsize=(10, 5))

# Fetch and plot each signal with thinner lines
for shot in all_shots:
    params_signal = {
        "signalName": signal_name,
        "shotNumber": shot
    }

    response_signal = requests.get(server_url_signal, params=params_signal)

    if response_signal.status_code == 200:
        response_text = response_signal.text.strip()

        # Extract time and amplitude values
        try:
            lines = response_text.split("\n")
            times, amplitudes = [], []
            for line in lines:
                parts = line.split(",")
                if len(parts) == 2:
                    t, amp = float(parts[0]), float(parts[1])
                    times.append(t)
                    amplitudes.append(amp)

            times = np.array(times)
            amplitudes = np.array(amplitudes)

            if len(amplitudes) == 0:
                continue

            # ✅ **Plot with thinner lines for better visibility**
            plt.plot(times, amplitudes, label=f"Shot {shot}", linewidth=0.5)

        except ValueError:
            continue

plt.xlabel("Tiempo")
plt.ylabel("Amplitud")
plt.title(f"Señal {signal_name} y sus 5 señales más similares")
plt.legend()
plt.show()