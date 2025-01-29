import pandas as pd
from langchain_community.llms import Replicate
from dotenv import load_dotenv
from googletrans import Translator
import asyncio
import os
import nest_asyncio
import pandasql as ps

nest_asyncio.apply()

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
    "Always use 'N_DESCARGA' as the column for filtering by number.\n"
    "Questions may be in Spanish or English, but the output must always be a valid SQL query.\n"
    "Do not include any explanations, greetings, or additional text in your response. Only output the SQL query."
)

# Spanish questions
questions = [
    "Cual es la fecha para el numero de descarga 4?",
    "cual es la hora para el numero de descarga 26458?",
    "cual es el comentario para el numero de descarga 8621?"
]

# Helper function to execute SQL queries on the DataFrame
def execute_sql_query(data, sql_query):
    try:
        # Use pandasql to execute SQL queries
        result = ps.sqldf(sql_query, locals())
        return result
    except Exception as e:
        return f"SQL Execution Error: {e}"

# Translate questions and process them
async def process_questions():
    translator = Translator()

    print("\nResults:")
    for question in questions:
        try:
            # Translate the question to English
            translated_question = await translator.translate(question, src='es', dest='en')

            # Provide the script and the translated question to the LLM
            llm_input = f"{script_context}\nConvert the following question into an SQL query: {translated_question.text}"

            # Get the generated SQL query from LLaMA-2
            response = llm.invoke(input=llm_input).strip()  # Extract and clean the response

            # Validate the SQL query
            if not response.strip().upper().startswith("SELECT"):
                print(f"Invalid SQL query generated for question: {question}")
                continue

            # Execute the SQL query on the DataFrame
            result = execute_sql_query(data, response)

            # Output only the question and the result
            print(f"Question (Original): {question}")
            print(f"Question (Translated): {translated_question.text}")
            print(f"Answer: {result}\n")

        except Exception as e:
            print(f"Error during processing for question '{question}': {e}\n")

# Run the processing function in an existing event loop
try:
    loop = asyncio.get_running_loop()
    task = loop.create_task(process_questions())
    loop.run_until_complete(task)
except RuntimeError:
    asyncio.run(process_questions())