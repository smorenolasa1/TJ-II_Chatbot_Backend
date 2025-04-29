import pandas as pd
import json
import os
import nest_asyncio
import numpy as np
import pandasql as ps
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_community.llms import Replicate
from words import process_query  # Import words.py function
import re
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
import json

CONTEXT_DIR = "context"
os.makedirs(CONTEXT_DIR, exist_ok=True)

nest_asyncio.apply()

# Initialize FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Load environment variables
load_dotenv()

# Set up Replicate for LLaMA-2
os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")
llama2_13b_chat = "meta/meta-llama-3-8b-instruct"

llm = Replicate(
    model=llama2_13b_chat,
    model_kwargs={"temperature": 0.7, "max_new_tokens": 100}
)

# Load Google API Key from .env file
google_api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=google_api_key)

# Set up Gemini AI model
MODEL_NAME = "models/gemini-1.5-pro"
model = genai.GenerativeModel(MODEL_NAME)

# Load JSON file while preserving missing fields
file_path = "data/PARAMETROS_TJ2_model_time.json"

with open(file_path, "r", encoding="utf-8") as f:
    raw_json_data = json.load(f)

# Convert JSON list to DataFrame without inserting NaN
data = pd.DataFrame.from_records(raw_json_data)
data = data.astype(str).replace({"nan": None, "None": None, np.nan: None})

def save_csvupdate_context(question, response=None):
    CONTEXT_DIR = "context"
    os.makedirs(CONTEXT_DIR, exist_ok=True)
    context_file = os.path.join(CONTEXT_DIR, "csvupdate_history.json")

    print("📝 Saving CSV context...")
    print(f"📌 Question: {question}")
    print(f"📌 Response: {response}")

    new_entry = {
        "question": question,
        "response": response
    }

    try:
        if os.path.exists(context_file):
            print("📂 File exists, loading...")
            with open(context_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            print("📁 File does not exist, creating new...")
            history = []

        history.append(new_entry)

        with open(context_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
        print(f"✅ CSV context saved to {context_file}")

    except Exception as e:
        print(f"❌ Error saving CSV context: {e}")

# Helper function to execute SQL queries dynamically
def execute_sql_query(data, sql_query):
    try:
        result = ps.sqldf(sql_query, {"data": data})

        if result.empty:
            raise HTTPException(status_code=404, detail="No matching records found.")

        cleaned_result = [
            {k: v for k, v in record.items() if v is not None} 
            for record in result.to_dict(orient="records")
        ]

        return cleaned_result

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL Execution Error: {e}")

# Define request model for the API
class Question(BaseModel):
    question: str
    parameters: dict = None  # Structured parameters

# Temporary storage for active conversation (reset after query execution)
active_conversation = {}

@app.post("/get_csv_answer")
def ask_question(question: Question):
    global active_conversation  # Use global scope to reset after processing
    
    try:
        print(f"Received question: {question.question}")

        clarifications_needed = {}

        # If a conversation is ongoing and user is clarifying
        if active_conversation and "extracted_keywords" in active_conversation:
            # Fix: Extract only the selected value, not the entire phrase
            user_selected_values = [value.strip().split(":")[-1].strip() for value in question.question.split(",")]    # Trim spaces
            expected_keys = [key for key, value in active_conversation["extracted_keywords"].items() if len(value) > 1]
            
            print(f"[DEBUG] Expected Keys: {expected_keys}")
            print(f"[DEBUG] User Selected Values: {user_selected_values}")

            if len(user_selected_values) > len(expected_keys):
                return {"message": "Too many values provided. Please match the number of clarifications requested."}

            # Update the final mapping based on user selection
            for i, key in enumerate(user_selected_values):
                if i < len(expected_keys):  # Ensure we do not exceed the expected keys
                    active_conversation["final_keyword_mapping"][expected_keys[i]] = [key]

            print(f"[DEBUG] Updated Final Keyword Mapping: {active_conversation['final_keyword_mapping']}")

        else:
            # New question: Process normally
            extracted_keywords = process_query(question.question)

            if not extracted_keywords or extracted_keywords == "No matching parameters found.":
                return {"message": "No relevant parameters found. Please specify."}

            # Store extracted keywords in the active conversation
            active_conversation = {
                "original_question": question.question,  # Store original question
                "extracted_keywords": extracted_keywords,
                "final_keyword_mapping": {}
            }

            # Check for columns that need clarification
            clarifications_needed = {}
            for key, matches in extracted_keywords.items():
                if len(matches) == 1:
                    active_conversation["final_keyword_mapping"][key] = matches  # Store directly if only one option
                else:
                    clarifications_needed[key] = matches

            # If clarifications are needed, ask the user for all at once
            if clarifications_needed:
                clarification_messages = [f"{key}: {', '.join(matches)}" for key, matches in clarifications_needed.items()]
                return {"clarification": clarification_messages}

        # Extract column names for SQL
        column_names = [col for cols in active_conversation["final_keyword_mapping"].values() for col in cols]

        print(f"[DEBUG] Column Names: {column_names}")
        # Print active conversation before sending to LLM
        print(f"[DEBUG] LLM Input Being Sent: \nUser's question: '{active_conversation.get('original_question', '')}'.\n")        

        # Use the original question when sending to the LLM, even after clarifications
        llm_input = (
            "La tabla se llama 'data'.\n"
            f"Pregunta del usuario: '{active_conversation.get('original_question', '')}'.\n"
            f"Las columnas disponibles son: {', '.join(column_names)}.\n"
            "Genera una consulta SQL válida usando SOLO y exclusivamente los nombres de estas columnas disponibles.\n\n"

            "### Manejo de fechas ('fecha' en formato YYYY-MM-DD):\n"
            "- Para un **día específico** usa: `WHERE fecha = 'YYYY-MM-DD'`.\n"
            "- Para un **mes específico** usa: `WHERE strftime('%Y-%m', fecha) = 'YYYY-MM'`.\n"
            "- Para un **año específico** usa: `WHERE strftime('%Y', fecha) = 'YYYY'`.\n\n"

            "### Manejo de descargas:\n"
            "- Si el usuario menciona una **descarga específica**, como 'descarga 42452' o un número solo, usa `WHERE N_DESCARGA = '42452'`.\n"
            "- No uses otras columnas como `hora`, `pared`, `comentario`, etc. para buscar una descarga. Siempre usa `N_DESCARGA` para filtrar descargas.\n\n"

            "### Consideraciones adicionales:\n"
            "- Todos los números y celdas son strings.\n"
            "- Para contar descargas, usa `COUNT(N_DESCARGA)`.\n"
            "- Para agrupar por año, usa `GROUP BY strftime('%Y', fecha)`.\n"
            "- Para obtener solo el valor más alto, usa `ORDER BY total_descargas DESC LIMIT 1`.\n"
            "- Si el usuario menciona una configuración específica, filtra usando `configuracion`.\n\n"

            "Devuelve SOLO la consulta SQL válida, sin texto adicional."
        )

        response = llm.invoke(input=llm_input).strip()
        print(f"Raw LLM Response: {response}")

        # Extract only the SQL query
        match = re.search(r"```sql\s+(SELECT[\s\S]+?)\s+```", response, re.IGNORECASE)

        if match:
            sql_query = match.group(1).strip()  # Extracts only the SQL part
        else:
            sql_query = response.strip()  # Fallback if no backticks are present

        # Remove any trailing semicolon to prevent SQLite execution error
        sql_query = sql_query.rstrip(";")

        print(f"Cleaned SQL Query: {sql_query}")

        # Execute the SQL query
        result = execute_sql_query(data, sql_query)

        print(f"Final Filtered Query Result: {result}")

        # Reset active conversation after SQL execution
        active_conversation = {}
        result_text = json.dumps(result, indent=2)
        result_lines = result_text.split("\n")
        # If the result has more than 5 lines, return it directly without calling Gemini AI
        if len(result_lines) > 15:
            print("[DEBUG] SQL result is too long. Skipping Gemini AI and returning raw result.")
            return {"answer": result}

        # Otherwise, generate explanation with Gemini AI
        explanation_prompt = (
            "Eres un chatbot especializado en fusión nuclear\n"
            f"Pregunta original: {question.question}\n"
            "Resultado de la consulta SQL:\n"
            f"{result_text}\n\n"
            "Enseña el comentario como Respuesta, y después explica el resultado de manera clara y concisa para el usuario."
        )

        final_response = model.generate_content(explanation_prompt).text.strip()
        print(f"Final LLM Response: {final_response}")
        # Save context
        save_csvupdate_context(
            question=question.question,
            response=final_response
        )
        return {"answer": final_response}

    except Exception as e:
        print(f"Error during processing: {e}")
        active_conversation = {}  # Reset on failure too
        raise HTTPException(status_code=500, detail=f"Error during processing: {e}")