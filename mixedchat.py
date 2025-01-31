import requests
import matplotlib.pyplot as plt
import urllib3
import re
import streamlit as st
import json
from langchain_community.llms import Replicate
from dotenv import load_dotenv
import os

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
load_dotenv()
os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")

# Set up Replicate LLaMA-3
llm = Replicate(
    model="meta/meta-llama-3-8b-instruct",
    model_kwargs={"temperature": 0.1, "max_new_tokens": 100}
)

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

    **Example 3:**
    Input: "Show graph for shot 12345 with signals ElectronDensity and PlasmaCurrent"
    Output: {{"shot": 12345, "tstart": null, "tstop": null, "signals": ["ElectronDensity", "PlasmaCurrent"]}}

    **Example 4:**
    Input: "Shot 56789 signals Ip and TFI between 50 and 3000 seconds"
    Output: {{"shot": 56789, "tstart": 50, "tstop": 3000, "signals": ["Ip", "TFI"]}}

    Now, extract structured data from the following input:
    "{user_input}"

    Provide ONLY the response in a valid JSON format. Do NOT include any extra text, explanations, or greetings.
    """

    response = llm.invoke(input=prompt).strip()

    try:
        print(response)
        parsed_data = json.loads(response)  # Convert response to JSON
        return parsed_data
    except json.JSONDecodeError:
        return None


def generate_url(base_url, shot, nsignal, signals, factors, tstart, tstop):
    """Generates a URL to fetch signal data."""
    
    tstart = 0 if tstart is None else tstart
    tstop = 2000 if tstop is None else tstop

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

def load_keywords(filename="keywords.txt"):
    with open(filename, "r", encoding="utf-8") as f:
        keywords = [line.strip().lower() for line in f if line.strip() and not line.startswith("#")]
    return keywords

def load_signal_options(filename="signal_options.txt"):
    """Loads valid signal names from a file."""
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

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
    print(user_input)

    keywords = load_keywords()
    valid_signals = load_signal_options()

    if st.button("Submit"):
        if any(keyword in user_input.lower() for keyword in keywords):
            # Use AI to interpret the request
            print("Entra a keywords")
            parsed_data = parse_user_input_with_ai(user_input)
            print(parsed_data)

            if parsed_data and "shot" in parsed_data:
                print("Entra a parse data")
                shot = parsed_data["shot"]
                tstart = parsed_data.get("tstart", 0)
                tstop = parsed_data.get("tstop", 2000)
                signals = parsed_data.get("signals", [])

                # Filtrar señales válidas
                signals = [sig for sig in signals if sig in valid_signals]

                if signals:
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
                    st.error("No valid signals found in your request.")
            else:
                st.error("Failed to interpret your request. Please try again with a clearer format.")
        else:
            response = ask_api(user_input)
            if response:
                st.success("Response from API:")
                st.write(response)
            else:
                st.error("Failed to retrieve a response from the API.")

if __name__ == "__main__":
    main()