import requests
import matplotlib.pyplot as plt
import numpy as np

# User input
signal_name = "Densidad2_"
shot_number = "56900"

# Endpoint to get similar signals
server_url_similar = "http://localhost:8080/Servlet4"
params_similar = {
    "dbDirectory": "primitive_DB",
    "dbName": signal_name,
    "signalName": signal_name,
    "shotNumber": shot_number,
    "tIni": "1020",
    "tFin": "1025",
    "match": "32"
}

# Get response from the server
response_similar = requests.get(server_url_similar, params=params_similar)
response_text = response_similar.text.strip().split("\n")

# Filter and extract confidence & shot numbers
filtered_lines = [line.strip() for line in response_text[2:] if len(line.split()) >= 4]

similar_shots = []
for line in filtered_lines[:4]:  # top 4
    parts = line.split()
    shot = parts[0]
    tIni = float(parts[1].replace(",", "."))
    duration = float(parts[2].replace(",", "."))
    confidence = float(parts[3].replace(",", "."))
    tFin = tIni + duration
    similar_shots.append((confidence, shot, tIni, tFin))

# ✅ Print only the confidence, shot, and pattern range
print("✅ Resultados similares:")
for confidence, shot, tIni, tFin in similar_shots:
    print(f"{confidence:.4f}".replace(".", ",") + f" - {shot} - [{str(tIni).replace('.', ',')} , {str(tFin).replace('.', ',')}]")

# Endpoint to fetch the signal data
server_url_signal = "http://localhost:8080/Servlet7"

# List of all shots to plot
all_shots = [shot[1] for shot in similar_shots]

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

            if len(amplitudes) > 0:
                plt.plot(times, amplitudes, label=f"Shot {shot}", linewidth=0.5)

        except ValueError:
            continue

plt.xlabel("Tiempo")
plt.ylabel("Amplitud")
plt.title(f"Señal {signal_name} y sus 4 señales más similares")
plt.legend()
plt.show()