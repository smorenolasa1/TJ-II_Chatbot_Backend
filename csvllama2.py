import pandas as pd
from langchain_community.llms import Replicate
from dotenv import load_dotenv
import os
import nest_asyncio
import pandasql as ps
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.logger import logger
import traceback

nest_asyncio.apply()

# Initialize FastAPI
app = FastAPI()

# Load environment variables
load_dotenv()

# Set up Replicate for LLaMA-2
os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")
llama2_13b_chat = "meta/llama-2-7b-chat"

llm = Replicate(
    model=llama2_13b_chat,
    model_kwargs={"temperature": 0.7, "max_new_tokens": 100}
)

# Load the CSV file
file_path = "data/PARAMETROS_TJ2_ORDENADOS.csv"  # Replace with your file path
data = pd.read_csv(file_path, delimiter=";", encoding="latin1", low_memory=False)

# Ensure missing values are replaced properly
for column in data.columns:
    if data[column].dtype == "float64":
        data[column] = data[column].fillna(-1)
        if column == "N_DESCARGA":
            data[column] = data[column].astype(int)
    else:
        data[column] = data[column].fillna("N/A")

# Convert the entire DataFrame to strings
data = data.astype(str)

# Define the column names and script as context
script_context = (
    "The table is named 'data' and contains the following important columns:\n"
    "N_DESCARGA, fecha, hora, comentarioDesc, comentarioExp, configuracion, "
    "potencia_radiada, energia_diamagnetica.\n"
    "You must use these column names exactly as they are when writing SQL queries.\n"
    "JUST OUTPUT THE SQL QUERY, NOTHING ELSE, no sure i´d be happy to help, JUST THE SQL QUERY\n"
    "E.g.,: SELECT hora FROM data WHERE N_DESCARGA = ´26458`;"
    "Questions must be in English, and the output must always be a valid SQL query.\n"
    "Strictly output only the SQL query with no additional text, explanation, or formatting."
)

# Helper function to execute SQL queries on the DataFrame
def execute_sql_query(data, sql_query):
    try:
        # Use pandasql to execute SQL queries
        result = ps.sqldf(sql_query, locals())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL Execution Error: {e}")

# Define request model for the API
class Question(BaseModel):
    question: str

@app.post("/ask")
def ask_question(question: Question):
    try:
        # Log the received question
        print(f"Received question: {question.question}")

        # Provide the script and the question directly to the LLM
        llm_input = f"{script_context}\nConvert the following question into an SQL query: {question.question}"
        print(f"LLM Input: {llm_input}")

        # Get the generated SQL query from LLaMA-2
        response = llm.invoke(input=llm_input).strip()
        print(f"Raw LLM Response: {response}")

        # Extract only the SQL query
        # Find the first line that starts with "SELECT" and remove any leading/trailing text
        sql_query = next((line.strip() for line in response.splitlines() if line.strip().upper().startswith("SELECT")), None)

        if not sql_query:
            raise HTTPException(status_code=400, detail="Invalid SQL query generated.")

        print(f"Cleaned SQL Query: {sql_query}")

        # Execute the SQL query on the DataFrame
        result = execute_sql_query(data, sql_query)
        print(f"Query execution result: {result}")

        # Return the query result
        return result.to_dict(orient="records")

    except Exception as e:
        # Log the detailed error
        print(f"Error during processing: {e}")
        raise HTTPException(status_code=500, detail=f"Error during processing: {e}")