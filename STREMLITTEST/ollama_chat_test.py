import streamlit as st
import ollama
import subprocess
import re
import os

def load_signal_options(filename):
    """
    Loads the list of signal options from the specified file.
    """
    try:
        with open(filename, "r") as file:
            return [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        st.error(f"Error: The file {filename} does not exist.")
        return []

# Load signal options
SIGNAL_OPTIONS = load_signal_options("signal_options.txt")

# Streamlit UI
st.title("Ollama Chat Interface")
st.write("Chat with Ollama. Type 'Exit' to end the conversation.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.text_input("You:")

if user_input:
    if user_input.lower() in ["exit", "salir"]:
        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("Bot", "Goodbye!!"))
        st.write("Goodbye!!")
    else:
        # Check if "número de descarga" or "shot number" is mentioned
        shot_match = re.search(r'(numero de descarga|shot number) (\d+)', user_input, re.IGNORECASE)
        if shot_match:
            shot = shot_match.group(2)
            matching_signals = [signal for signal in SIGNAL_OPTIONS if re.search(rf'\b{re.escape(signal)}\b', user_input)]

            if matching_signals:
                st.session_state.chat_history.append(("You", user_input))
                st.session_state.chat_history.append(("Bot", f"Running 'diagramasWeb.py' with shot {shot} and signals: {', '.join(matching_signals)}"))
                
                try:
                    subprocess.run([
                        "/Users/sofiamorenolasa/Desktop/TFGJaime/Shared_TFG/venv/bin/python", 
                        "diagramasWeb.py", 
                        "--shot", shot, 
                        "--signals"] + matching_signals, check=True)
                except subprocess.CalledProcessError as e:
                    st.error("There was an error running 'diagramasWeb.py': " + str(e))
            else:
                st.session_state.chat_history.append(("You", user_input))
                st.session_state.chat_history.append(("Bot", "No valid signals were found in the user's message."))
        else:
            # Generate response using Ollama
            response = ollama.generate(model='llama3', prompt=user_input)
            bot_response = response['response']
            st.session_state.chat_history.append(("You", user_input))
            st.session_state.chat_history.append(("Bot", bot_response))

# Display chat history
for speaker, message in st.session_state.chat_history:
    st.write(f"**{speaker}:** {message}")