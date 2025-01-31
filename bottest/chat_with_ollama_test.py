import streamlit as st
import requests
import threading
import time
import uvicorn
import atexit
from fastapi import FastAPI
from PIL import Image
from io import BytesIO
import base64

# Define the FastAPI app (this should be in another file normally)
app = FastAPI()

@app.post("/chat_with_ollama")
async def chat_with_ollama(data: dict):
    user_message = data.get("message", "")
    response_text = f"Echo: {user_message}"  # Replace this with actual AI logic

    # Example dummy response with an optional diagram
    response_data = {
        "response": response_text,
        "diagram_base64": None,  # Base64 image can be added here
    }
    return response_data

# Function to run Uvicorn server in a separate thread
def run_fastapi():
    uvicorn.run(app, host="127.0.0.1", port=8000)

# Start FastAPI server in a background thread if not already running
server_thread = threading.Thread(target=run_fastapi, daemon=True)
server_thread.start()
time.sleep(2)  # Give the server a moment to start

# Ensure server stops when Streamlit app exits
def stop_fastapi():
    print("Stopping FastAPI server...")

atexit.register(stop_fastapi)

# Streamlit UI
st.title("Chat with Ollama")

user_input = st.text_input("You: ")

if st.button("Send"):
    try:
        response = requests.post("http://127.0.0.1:8000/chat_with_ollama", json={"message": user_input})
        if response.status_code == 200:
            response_data = response.json()
            st.write(response_data["response"])

            # Display diagram if available
            if "diagram_url" in response_data:
                st.image(response_data["diagram_url"], caption="Ollama Diagram")
            elif "diagram_base64" in response_data and response_data["diagram_base64"]:
                image_data = base64.b64decode(response_data["diagram_base64"])
                image = Image.open(BytesIO(image_data))
                st.image(image, caption="Ollama Diagram")
        else:
            st.write("Error: ", response.json().get("detail", "Unknown error"))
    except requests.exceptions.ConnectionError:
        st.write("Error: Could not connect to the FastAPI server.")