import os
import json
from dotenv import load_dotenv
from langchain_community.llms import Replicate
import requests
import streamlit as st
import matplotlib.pyplot as plt
import re

# Load environment variables
load_dotenv()
os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")

# Set up Replicate LLaMA-2
os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")
llama2_13b_chat = "meta/meta-llama-3-8b-instruct"
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

    Now, extract structured data from the following input:
    "{user_input}"

    Provide ONLY the response in a valid JSON format. Do NOT include any extra text, explanations, or greetings.
    """

    response = llm.invoke(prompt).strip()

    try:
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