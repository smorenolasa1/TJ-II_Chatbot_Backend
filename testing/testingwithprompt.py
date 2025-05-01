import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Load API key from .env
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# UI setup
st.set_page_config(page_title="Ask Your CSV")
st.title("Ask about your CSV")

if not openai_api_key:
    st.error("❌ OPENAI_API_KEY not set. Please check your .env file.")
    st.stop()

# Upload CSV
uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

if uploaded_file:
    try:
        # Load the CSV
        df = pd.read_csv(
            uploaded_file,
            sep=";",
            encoding="latin1",
            quotechar='"',
            on_bad_lines="skip"
        )
        st.success(f"✅ CSV loaded with {df.shape[0]} rows and {df.shape[1]} columns!")

        # Show preview
        st.dataframe(df.head())

        # Ask user for question
        user_question = st.text_input("Ask a question about your CSV:")

        if user_question:
            with st.spinner("Thinking..."):
                # Convert DataFrame to text
                csv_snippet = df.head(10).to_csv(index=False)

                # Build prompt
                prompt = f"""
You are a helpful data analyst. A scientist has uploaded the following CSV data (only the first 10 rows are shown here):

{csv_snippet}

They asked the following question:
"{user_question}"

Please answer the question based on the data and explain your answer clearly. Use bullet points if needed. Be concise and precise.
"""

                # Use ChatOpenAI directly
                llm = ChatOpenAI(
                    temperature=0,
                    model="gpt-3.5-turbo",
                    openai_api_key=openai_api_key
                )

                # Call the model
                response = llm.predict(prompt)

                # Show response
                st.markdown("### 🤖 Answer")
                st.write(response)

    except Exception as e:
        st.error(f"❌ Error loading or processing CSV: {e}")