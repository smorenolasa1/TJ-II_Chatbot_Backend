import requests
import matplotlib.pyplot as plt
import urllib3
import re
import argparse

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def generate_url(base_url, shot, nsignal, signals, factors, tstart, tstop):
    """
    Generates a URL to make a request based on the provided parameters.
    """
    url = f"{base_url}?shot={shot}&nsignal={nsignal}"
    
    for i in range(1, nsignal + 1):
        signal = signals[i - 1] if i - 1 < len(signals) else ""
        factor = factors[i - 1] if i - 1 < len(factors) else "1.00"
        url += f"&signal{i:02}={signal}&fact{i:02}={factor}"

    url += f"&tstart={tstart:.2f}&tstop={tstop:.2f}"
    return url

def fetch_data(url):
    """
    Makes an HTTP GET request to the generated URL and returns the response.
    """
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        print("Full server response:")
        print(response.text[:1000])  # Displays the first 1000 characters
        return response.text
    else:
        raise ValueError(f"Error connecting to the server: {response.status_code}")

def extract_data_points(html_content, signals):
    """
    Extracts the data contained in `dataXX` from the received HTML for multiple signals.
    If a signal has no data, it displays a message indicating that it was not found.
    """
    data_points_dict = {}
    matches = re.finditer(r"var data(\d{2}) = \[(.*?)\];", html_content, re.DOTALL)
    for signal_name in signals:
        if not signal_name.strip():
            continue
        match = next((m for m in matches if f"var data{signals.index(signal_name)+1:02}" in m.group(0)), None)
        if not match:
            print(f"Warning: No data found for the signal '{signal_name}'.")
            continue
        data_block = match.group(2)
        # Parse the data into a list of tuples
        data_points = []
        for line in data_block.split('],['):
            values = line.strip('[]').split(',')
            x, y = map(float, values)
            data_points.append((x, y))
        data_points_dict[signal_name] = data_points
    
    if not data_points_dict:
        raise ValueError("No valid data found for the provided signals.")

    return data_points_dict

def plot_data_per_signal(data_points_dict):
    """
    Generates individual graphs for each signal.
    """
    for signal_name, data_points in data_points_dict.items():
        x_values = [point[0] for point in data_points]
        y_values = [point[1] for point in data_points]

        plt.figure(figsize=(10, 6))
        plt.plot(x_values, y_values, label=signal_name, linewidth=1.5)
        plt.title(f"Graph for Signal: {signal_name}")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.legend()
        plt.grid()
        plt.show()

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process and plot data for specific signals.")
    parser.add_argument("--shot", type=int, required=True, help="Shot number (e.g., 57547)")
    parser.add_argument("--signals", nargs="+", required=True, help="List of signals (e.g., TFI Densidad2_)")
    parser.add_argument("--tstart", type=float, default=0.00, help="Start time (default: 0.00)")
    parser.add_argument("--tstop", type=float, default=2000.00, help="Stop time (default: 2000.00)")
    args = parser.parse_args()

    # Configure parameters
    shot = args.shot
    signals = args.signals
    nsignal = max(len(signals), 5)  # Ensure nsignal is at least 5
    factors = ["1.00"] * nsignal  # Default factors for all signals
    tstart = args.tstart
    tstop = args.tstop

    # Base URL
    base_url = "https://info.fusion.ciemat.es/cgi-bin/TJII_data.cgi"

    # Generate URL
    generated_url = generate_url(base_url, shot, nsignal, signals, factors, tstart, tstop)
    print("Generated URL:", generated_url)

    # Fetch and process data
    try:
        raw_html = fetch_data(generated_url)
        data_points_dict = extract_data_points(raw_html, signals)
        print("Extracted data:", {k: v[:5] for k, v in data_points_dict.items()})  # Shows the first 5 points of each signal
        plot_data_per_signal(data_points_dict)
    except Exception as e:
        print("Error processing the diagram:", e)

if __name__ == "__main__":
    main()

