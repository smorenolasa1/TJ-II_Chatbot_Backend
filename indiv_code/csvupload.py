import streamlit as st
from dotenv import load_dotenv
import os
import pandas as pd
import google.generativeai as genai

# Configure Streamlit page
st.set_page_config(page_title="Ask your CSV (Google Gemini)")

def main():
    # Load environment variables
    load_dotenv()

    # Get Google API Key
    google_api_key = os.getenv("GOOGLE_API_KEY")

    # Validate API Key
    if not google_api_key:
        st.error("❌ GOOGLE_API_KEY is not set. Please check your .env file.")
        return

    st.success("✅ GOOGLE_API_KEY is set")

    st.header("📊 Ask your CSV (Powered by Google Gemini AI)")

    # Configure Google API Key
    genai.configure(api_key=google_api_key)

    # Use the correct model for your API key
    model_name = "models/gemini-1.5-pro"

    # Upload CSV file
    csv_file = st.file_uploader("📂 Upload a CSV file", type=["csv"])
    
    if csv_file is not None:
        try:
            # Detect delimiter: "," or ";"
            first_line = csv_file.read(5000).decode("latin1").split("\n")[0]
            delimiter = ";" if ";" in first_line else ","
            csv_file.seek(0)  # Reset file pointer

            # Load CSV file into Pandas DataFrame
            df = pd.read_csv(csv_file, delimiter=delimiter, encoding="latin1")

            # Display Data Preview
            st.write("📊 Preview of the CSV data:")
            st.dataframe(df.head())

            # User input for CSV question
            user_question = st.text_input("🔍 Ask a question about your CSV:")

            if user_question:
                with st.spinner(text="⏳ Thinking..."):
                    # Convert DataFrame to a string for better AI interaction
                    csv_data = df.to_csv(index=False)

                    # Prepare query with context
                    query = f"The following CSV data has been uploaded:\n{csv_data}\n\nAnswer this question based on the data: {user_question}, and respond to the user in the same language as the question."

                    # Send request to Gemini AI
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(query)

                    st.write(response.text)

        except Exception as e:
            st.error(f"❌ Error reading CSV: {e}")

if __name__ == "__main__":
    main()