import requests
import matplotlib.pyplot as plt
import urllib3
import re
import streamlit as st

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def generate_url(base_url, shot, nsignal, signals, factors, tstart, tstop):
    """Generates a URL to fetch signal data."""
    url = f"{base_url}?shot={shot}&nsignal={nsignal}"
    for i in range(1, nsignal + 1):
        signal = signals[i - 1] if i - 1 < len(signals) else ""
        factor = factors[i - 1] if i - 1 < len(factors) else "1.00"
        url += f"&signal{i:02}={signal}&fact{i:02}={factor}"
    url += f"&tstart={tstart:.2f}&tstop={tstop:.2f}"
    return url

def fetch_data(url):
    """Fetches data from the URL."""
    response = requests.get(url, verify=False)
    return response.text if response.status_code == 200 else None

def extract_data_points(html_content, signals):
    """Extracts data from HTML content."""
    data_points_dict = {}
    matches = list(re.finditer(r"var data(\d{2}) = \[(.*?)\];", html_content, re.DOTALL))
    for signal_name in signals:
        match = next((m for m in matches if f"var data{signals.index(signal_name)+1:02}" in m.group(0)), None)
        if match:
            data_block = match.group(2)
            data_points = [tuple(map(float, line.strip('[]').split(','))) for line in data_block.split('],[')]
            data_points_dict[signal_name] = data_points
    return data_points_dict

def plot_data_per_signal(data_points_dict):
    """Plots signal data."""
    for signal_name, data_points in data_points_dict.items():
        x_values, y_values = zip(*data_points)
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(x_values, y_values, label=signal_name, linewidth=1.5)
        ax.set_title(f"Graph for Signal: {signal_name}")
        ax.set_xlabel("Time")
        ax.set_ylabel("Value")
        ax.legend()
        ax.grid()
        st.pyplot(fig)
        plt.close(fig)

def ask_api(question):
    """Sends a question to the external API."""
    response = requests.post("http://localhost:8000/ask", json={"question": question})
    return response.json() if response.status_code == 200 else None

def main():
    st.title("Unified TJ-II Chatbot")
    user_input = st.text_input("Ask a question or request a plot:")
    
    if st.button("Submit"):
        if any(keyword in user_input.lower() for keyword in ["plot", "diagram", "diagrama"]):
            match = re.search(r"shot (\d+) from (\d+) to (\d+)", user_input)
            signals_match = re.findall(r"plot (.+) for", user_input, re.IGNORECASE)
            
            if match and signals_match:
                shot = int(match.group(1))
                tstart = float(match.group(2))
                tstop = float(match.group(3))
                signals = [s.strip() for s in signals_match[0].split(" and ")]
                
                nsignal = max(len(signals), 5)
                factors = ["1.00"] * nsignal
                base_url = "https://info.fusion.ciemat.es/cgi-bin/TJII_data.cgi"
                
                url = generate_url(base_url, shot, nsignal, signals, factors, tstart, tstop)
                html_content = fetch_data(url)
                if html_content:
                    data_points_dict = extract_data_points(html_content, signals)
                    plot_data_per_signal(data_points_dict)
                else:
                    st.error("No data retrieved for the requested shot and signals.")
            else:
                st.error("Invalid input format for plotting. Try: 'Plot TFI and Densidad2_ for shot 57547 from 0 to 2000'")
        else:
            if user_input.strip():
                # Send the question to the API endpoint
                response = requests.post(
                    "http://localhost:8000/ask",  # Adjust to your server URL
                    json={"question": user_input},
                )

                if response.status_code == 200:
                    st.success("Query executed successfully!")
                    st.write("Result:")
                    st.dataframe(response.json())
                else:
                    st.error("An error occurred:")
                    st.write(response.text)
            else:
                st.warning("Please enter a question before submitting.")
if __name__ == "__main__":
    main()