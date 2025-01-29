# custom_chat.py
import streamlit as st
import requests

def main():
    st.title("TJ-II Chatbot")

    # Input box for user question
    question = st.text_input("Enter your question (in Spanish or English):")

    # Submit button
    if st.button("Ask Question"):
        if question.strip():
            # Send the question to the API endpoint
            response = requests.post(
                "http://localhost:8000/ask",  # Adjust to your server URL
                json={"question": question},
            )

            if response.status_code == 200:
                st.success("Query executed successfully!")
                st.write("Result:")
                st.dataframe(response.json())
            else:
                st.error("An error occurred:")
                st.write(response.text)
        else:
            st.warning("Please enter a question before submitting.")

if __name__ == "__main__":
    main()