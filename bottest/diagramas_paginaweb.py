import requests
import matplotlib.pyplot as plt
import urllib3
import re
import streamlit as st

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
        return response.text
    else:
        st.error(f"Error connecting to the server: {response.status_code}")
        return None

def extract_data_points(html_content, signals):
    """
    Extracts the data contained in `dataXX` from the received HTML for multiple signals.
    """
    data_points_dict = {}
    matches = list(re.finditer(r"var data(\d{2}) = \[(.*?)\];", html_content, re.DOTALL))
    
    for signal_name in signals:
        if not signal_name.strip():
            continue
        match = next((m for m in matches if f"var data{signals.index(signal_name)+1:02}" in m.group(0)), None)
        if not match:
            st.warning(f"No data found for the signal '{signal_name}'.")
            continue
        data_block = match.group(2)
        data_points = []
        for line in data_block.split('],['):
            values = line.strip('[]').split(',')
            try:
                x, y = map(float, values)
                data_points.append((x, y))
            except ValueError:
                continue
        data_points_dict[signal_name] = data_points
    
    if not data_points_dict:
        st.error("No valid data found for the provided signals.")
    
    return data_points_dict

def plot_data_per_signal(data_points_dict):
    """
    Generates and displays individual graphs for each signal in Streamlit.
    """
    for signal_name, data_points in data_points_dict.items():
        x_values = [point[0] for point in data_points]
        y_values = [point[1] for point in data_points]

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(x_values, y_values, label=signal_name, linewidth=1.5)
        ax.set_title(f"Graph for Signal: {signal_name}")
        ax.set_xlabel("Time")
        ax.set_ylabel("Value")
        ax.legend()
        ax.grid()

        st.pyplot(fig)
        plt.close(fig)

def main():
    st.title("Signal Data Visualization")
    
    user_input = st.text_input("Enter your request:", "Plot TFI and Densidad2_ for shot 57547 from 0 to 2000")
    
    if st.button("Generate Graphs"):
        import re
        match = re.search(r"shot (\d+) from (\d+) to (\d+)", user_input)
        signals_match = re.findall(r"Plot (.+) for", user_input)
        
        if not match or not signals_match:
            st.error("Could not understand the input format. Please use natural language like 'Plot TFI and Densidad2_ for shot 57547 from 0 to 2000'")
            return
        
        shot = int(match.group(1))
        tstart = float(match.group(2))
        tstop = float(match.group(3))
        signals = [s.strip() for s in signals_match[0].split(" and ")]
        
        nsignal = max(len(signals), 5)
        factors = ["1.00"] * nsignal
        base_url = "https://info.fusion.ciemat.es/cgi-bin/TJII_data.cgi"
        
        try:
            generated_url = generate_url(base_url, shot, nsignal, signals, factors, tstart, tstop)
            raw_html = fetch_data(generated_url)
            if raw_html is None:
                return
            data_points_dict = extract_data_points(raw_html, signals)
            if data_points_dict:
                plot_data_per_signal(data_points_dict)
            else:
                st.error("No plots generated due to missing data.")
        except Exception as e:
            st.error(f"Error processing the diagram: {e}")

if __name__ == "__main__":
    main()