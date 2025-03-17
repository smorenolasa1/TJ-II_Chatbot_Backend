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

nest_asyncio.apply()

# Initialize FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to ["http://localhost:3000"] if you want to be strict
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

# Load JSON file while preserving missing fields
file_path = "data/PARAMETROS_TJ2_model_time.json"

with open(file_path, "r", encoding="utf-8") as f:
    raw_json_data = json.load(f)

# Convert JSON list to DataFrame without inserting NaN
data = pd.DataFrame.from_records(raw_json_data)
data = data.astype(str).replace({"nan": None, "None": None, np.nan: None})

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
            user_selected_values = [value.strip() for value in question.question.split(",")]  # Trim spaces
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

        print(f"[DEBUG] Final Keyword Mapping After Clarifications: {active_conversation['final_keyword_mapping']}")
        print(f"[DEBUG] Column Names: {column_names}")
        # Print active conversation before sending to LLM
        print(f"[DEBUG] LLM Input Being Sent: \nUser's question: '{active_conversation.get('original_question', '')}'.\n")        

        # Use the **original question** when sending to the LLM, even after clarifications
        llm_input = (
            "La tabla se llama 'data'.\n"
            f"Pregunta del usuario: '{active_conversation.get('original_question', '')}'.\n"
            f"Las columnas disponibles son: {', '.join(column_names)}.\n"
            "Genera una consulta SQL válida usando exclusivamente estas columnas.\n"
            
            "### Manejo de fechas ('fecha' en formato YYYY-MM-DD):\n"
            "- Para un **día específico** usa: `WHERE fecha = 'YYYY-MM-DD'`.\n"
            "- Para un **mes específico** usa: `WHERE strftime('%Y-%m', fecha) = 'YYYY-MM'`.\n"
            "- Para un **año específico** usa: `WHERE strftime('%Y', fecha) = 'YYYY'`.\n"
            
            "### Consideraciones adicionales:\n"
            "Todos los numeros y celdas son strings"
            "- Si se requiere contar descargas, usa `COUNT(N_DESCARGA)`.\n"
            "- Para agrupar por año, usa `GROUP BY strftime('%Y', fecha)`.\n"
            "- Si se necesita obtener solo el valor más alto, usa `ORDER BY total_descargas DESC LIMIT 1`.\n"
            "Si el usuario menciona una configuración específica, filtra con la columna `configuracion`.\n"
            "Devuelve SOLO la consulta SQL sin texto adicional."
        )

        response = llm.invoke(input=llm_input).strip()
        print(f"Raw LLM Response: {response}")

        # Extract only the SQL query
        match = re.search(r"SELECT[\s\S]+", response, re.IGNORECASE)
        sql_query = match.group(0).strip() if match else None

        if not sql_query:
            raise HTTPException(status_code=400, detail="Invalid SQL query generated.")

        print(f"Cleaned SQL Query: {sql_query}")

        # Execute the SQL query
        result = execute_sql_query(data, sql_query)

        print(f"Final Filtered Query Result: {result}")

        # Reset active conversation after SQL execution
        active_conversation = {}

        return {"answer": result}

    except Exception as e:
        print(f"Error during processing: {e}")
        active_conversation = {}  # Reset on failure too
        raise HTTPException(status_code=500, detail=f"Error during processing: {e}")