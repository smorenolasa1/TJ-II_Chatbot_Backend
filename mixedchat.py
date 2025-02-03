import requests
import urllib3
import streamlit as st
from shotllama2 import parse_user_input_with_ai, generate_url, fetch_data, extract_data_points, load_keywords, plot_data_per_signal
from shotllama2 import load_signal_options

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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