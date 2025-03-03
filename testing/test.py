import os
import json
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_openai import OpenAI
from sqlalchemy import create_engine
import nest_asyncio
from words import process_query
import re

nest_asyncio.apply()

# Initialize FastAPI
app = FastAPI()

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI LLM
llm = OpenAI(api_key=openai_api_key, temperature=0.7)

# Load JSON dataset into Pandas DataFrame
file_path = "data/PARAMETROS_TJ2_model_time.json"

with open(file_path, "r", encoding="utf-8") as f:
    raw_json_data = json.load(f)

data = pd.DataFrame.from_records(raw_json_data)
data = data.astype(str).replace({"nan": None, "None": None, np.nan: None})

# Convert Pandas DataFrame to SQLite (for LangChain SQL processing)
engine = create_engine("sqlite:///:memory:")
data.to_sql("data", engine, index=False, if_exists="replace")

# Get correct table name dynamically
table_names = engine.dialect.get_table_names(engine.connect())  # Correct method
if not table_names:
    table_names = engine.inspect(engine).get_table_names()  # Fallback method
if not table_names:
    raise ValueError("No tables found in SQLite database!")

table_name = table_names[0]  # Assuming there's only one table

# Print table names & schema to verify
print(f"✅ Table Name: {table_name}")
print(pd.read_sql(f"PRAGMA table_info({table_name});", engine))  # Print column names
print(pd.read_sql("PRAGMA table_info(data);", engine))
# Correct SQLDatabase import & usage
db = SQLDatabase(engine)

# Initialize SQLDatabaseToolkit with explicit table name
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# Use `create_sql_agent` with explicit table reference
sql_agent = create_sql_agent(llm, toolkit, verbose=True, prefix=f"Use the table {table_name}")

# Define request model
class Question(BaseModel):
    question: str

@app.post("/ask")
def ask_question(question: Question):
    try:
        print(f"Received question: {question.question}")

        # Step 1: Process the user's query to extract keywords and map them to column names using words.py
        relevant_keys = process_query(question.question)

        if not relevant_keys:
            return {"message": "No matching parameters found."}

        print(f"Mapped columns: {relevant_keys}")  # Debugging output

        # Step 2: Generate a dynamic SQL query using only the relevant columns
        prompt = f"The datasets name is called data. You have to create a SQL query using these column names exactly: {relevant_keys}, generate a SQL query for the question: {question.question}. E.g.,"

        # Step 3: Generate SQL query using LangChain's SQL agent and the mapped columns
        response = sql_agent.invoke(prompt)

        # Extract the SQL query from the response dictionary
        sql_query = response.get('output', None)

        if not sql_query:
            return {"message": "Error: No valid SQL query generated."}

        print(f"Generated SQL Query: {sql_query}")

        # Ensure that the generated SQL is correctly referencing the 'data' table
        sql_query = sql_query.replace("descarga", "data").replace("YEAR(N_DESCARGA)", "strftime('%Y', N_DESCARGA)").replace("COUNT(N_DESCARGA)", "COUNT(*)")

        # Execute the cleaned SQL query
        result = pd.read_sql(sql_query, engine).to_dict(orient="records")
        print(f"Result: {result}")

        if not result:
            return {"message": "No matching records found."}

        return result

    except Exception as e:
        print(f"Error during processing: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)