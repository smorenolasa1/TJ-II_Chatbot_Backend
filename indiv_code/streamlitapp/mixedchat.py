import requests
import urllib3
import streamlit as st
import time
import subprocess  # Para ejecutar otro script
from indiv_code.streamlitapp.shotllama2 import parse_user_input_with_ai, generate_url, fetch_data, extract_data_points, load_keywords, plot_data_per_signal
from indiv_code.streamlitapp.shotllama2 import load_signal_options

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def ask_api(question):
    """Sends a question to the main API (csvllama2)."""
    response = requests.post("http://localhost:8000/csv/ask", json={"question": question})
    return response.json() if response.status_code == 200 else None

def ask_api_pellet(question):
    """Sends a question to the pellet API."""
    response = requests.post("http://localhost:8000/pellet/ask", json={"question": question})
    return response.json() if response.status_code == 200 else None

def generate_report():
    """Executes report.py via Streamlit, waits for completion, and then runs pdf.py."""
    try:
        # Step 1: Start the Streamlit app properly using `streamlit run`
        process = subprocess.Popen(["streamlit", "run", "report.py"])
        st.success("Report interface started! Please complete the report in the Streamlit app.")

        # Step 2: Wait for user to complete report
        st.info("Waiting for report completion...")
        process.wait()  # Wait until the user finishes interacting with report.py

        time.sleep(2)  # Small delay to ensure report responses are saved

        # Step 3: Generate the PDF after report is completed
        subprocess.run(["python", "pdf.py"], check=True)
        st.success("PDF report successfully generated!")

    except subprocess.CalledProcessError as e:
        st.error(f"Error during report or PDF generation: {e}")

def main():
    st.title("Unified TJ-II Chatbot")
    user_input = st.text_input("Ask a question or request a plot:")
    print(user_input)

    keywords = load_keywords()
    valid_signals = load_signal_options()

    if st.button("Submit"):
        if "report" in user_input.lower():  
            st.info("Generating the report...")
            generate_report()

        elif any(keyword in user_input.lower() for keyword in keywords):
            # Use AI to interpret the request
            print("Entra a keywords")
            parsed_data = parse_user_input_with_ai(user_input)

            if parsed_data and "shot" in parsed_data:
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

        elif "pellet" in user_input.lower():  # Redirigir a pelletllama2.py si la pregunta menciona "pellet"
            response = ask_api_pellet(user_input)
            if response:
                st.success("Response from Pellet API:")
                st.write(response)
            else:
                st.error("Failed to retrieve a response from the Pellet API.")

        else:
            response = ask_api(user_input)
            if response:
                st.success("Response from API:")
                st.write(response)
            else:
                st.error("Failed to retrieve a response from the API.")

if __name__ == "__main__":
    main()