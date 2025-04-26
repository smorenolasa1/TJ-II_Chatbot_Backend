# FastAPI version of the provided Flask code
import os
import pandas as pd
import google.generativeai as genai
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
load_dotenv()

# Configure Google API Key
google_api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=google_api_key)

# Use the correct model
MODEL_NAME = "models/gemini-1.5-pro"

# Store dataset
stored_df = None
MAX_ROWS = 500

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global stored_df
    try:
        df = pd.read_csv(file.file)
        stored_df = df
        total_rows = len(stored_df)
        return {
            "message": "CSV uploaded successfully!",
            "total_rows": total_rows,
            "max_rows": MAX_ROWS
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Error processing file: {str(e)}"})

@app.post("/ask")
async def ask_question(request: Request):
    global stored_df
    try:
        data = await request.json()
        question = data.get("question")
        start_row = int(data.get("start_row", 0))
        end_row = int(data.get("end_row", MAX_ROWS))

        if not question:
            return JSONResponse(status_code=400, content={"error": "No question provided"})

        if stored_df is None:
            return JSONResponse(status_code=400, content={"error": "No dataset uploaded. Please upload a CSV first."})

        total_rows = len(stored_df)
        if start_row < 0 or end_row > total_rows or start_row >= end_row:
            return JSONResponse(status_code=400, content={"error": "Invalid row range selected."})

        selected_df = stored_df.iloc[start_row:end_row]
        csv_data = selected_df.to_csv(index=False)

        too_large_message = ""
        if total_rows > MAX_ROWS:
            too_large_message = f"\u26a0\ufe0f Your dataset has {total_rows} rows. We can only process {MAX_ROWS} rows at a time."

        query = f"""
        Se han subido los siguientes datos CSV (filas {start_row} a {end_row}):

        {csv_data}

        ### Instrucciones:
        - Analiza detenidamente los datos proporcionados y responde a la siguiente pregunta:
        **{question}**
        - Presenta la respuesta de forma clara y bien estructurada.
        - Usa viñetas (`-`) para listas.
        - Resalta los valores importantes usando negritas (`**`).
        - Utiliza subtítulos (##) si es necesario para organizar mejor la información.
        - Asegúrate de que la explicación sea concisa y evita repeticiones innecesarias.
        """
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(query)

        return {"response": response.text, "warning": too_large_message}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Server error: {str(e)}"})