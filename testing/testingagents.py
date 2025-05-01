import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from langchain_experimental.agents import create_pandas_dataframe_agent 
from langchain.chat_models import ChatOpenAI

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
        # ✅ Leer el CSV con separador personalizado y codificación
        df = pd.read_csv(
            uploaded_file,
            sep=";",
            encoding="latin1",
            quotechar='"',
            on_bad_lines="skip"  # Evita errores por filas con columnas desiguales
        )
        st.success(f"✅ CSV loaded with {df.shape[0]} rows and {df.shape[1]} columns!")

        # Crear el agente desde el DataFrame
        agent = create_pandas_dataframe_agent(
            ChatOpenAI(
                temperature=0,
                model="gpt-3.5-turbo",
                openai_api_key=openai_api_key
            ),
            df,
            verbose=True,
            allow_dangerous_code=True,
            handle_parsing_errors=True  # 👈 Añade esta línea
        )

        # Input del usuario
        question = st.text_input("Ask a question about your CSV:")

        if question:
            with st.spinner("Thinking..."):
                try:
                    response = agent.run(question)
                    st.markdown("### 🤖 Answer")
                    st.write(response)
                except Exception as e:
                    st.error(f"❌ Error generating answer: {e}")

    except Exception as e:
        st.error(f"❌ Error loading CSV file: {e}")