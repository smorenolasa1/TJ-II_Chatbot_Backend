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

nest_asyncio.apply()

# Initialize FastAPI
app = FastAPI()

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
file_path = "data/PARAMETROS_TJ2_model_clean.json"

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

# Global dictionary to store conversation history
conversation_history = {}

@app.post("/ask")
def ask_question(question: Question):
    try:
        print(f"Received question: {question.question}")

        # Find an existing conversation where the user is clarifying
        matching_question = next(
            (q for q in conversation_history if question.question in sum(conversation_history[q]["extracted_keywords"].values(), [])), 
            None
        )

        if matching_question:
            # Retrieve stored conversation
            conversation = conversation_history[matching_question]
            original_question = conversation["original_question"]

            # Merge clarification into existing mapping without overwriting other fields
            for key, matches in conversation["extracted_keywords"].items():
                if question.question in matches:
                    conversation["final_keyword_mapping"][key] = [question.question]

            print(f"[DEBUG] Clarification detected, updating final keyword mapping: {conversation['final_keyword_mapping']}")

        else:
            # First-time request: Process normally
            extracted_keywords = process_query(question.question)

            if not extracted_keywords or extracted_keywords == "No matching parameters found.":
                return {"message": "No relevant parameters found. Please specify."}

            # Store extracted keywords and initialize mapping
            conversation = {
                "original_question": question.question,
                "extracted_keywords": extracted_keywords,
                "final_keyword_mapping": {}
            }

            # Automatically assign fields when there’s only one match
            for key, matches in extracted_keywords.items():
                if len(matches) == 1:
                    conversation["final_keyword_mapping"][key] = matches
                else:
                    # Save conversation and ask user for clarification
                    conversation_history[question.question] = conversation
                    return {"message": f"Do you mean {', '.join(matches)}?"}

            original_question = question.question

        # Ensure all previous filters remain
        conversation["final_keyword_mapping"] = {
            **conversation["extracted_keywords"],  # Keep original extracted keywords
            **conversation["final_keyword_mapping"],  # Merge any clarifications
        }

        # Store updated conversation
        conversation_history[original_question] = conversation

        # Convert final keyword mapping into an explicit column replacement guide
        column_mapping_str = ", ".join(
            f"'{key}' should use column(s) {values}" for key, values in conversation["final_keyword_mapping"].items()
        )

        llm_input = (
            "The table is named 'data'.\n"
            f"User's original question: '{original_question}'.\n"
            f"Column mappings: {column_mapping_str}.\n"
            "Generate a valid SQL query using these exact column names.\n"
            "Output ONLY the SQL query."
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

        return result

    except Exception as e:
        print(f"Error during processing: {e}")
        raise HTTPException(status_code=500, detail=f"Error during processing: {e}")