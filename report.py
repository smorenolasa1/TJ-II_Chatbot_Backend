import os
import streamlit as st
from langchain_community.llms import Replicate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")

# Set up Replicate LLaMA-2
llama2_13b_chat = "meta/meta-llama-3-8b-instruct"
llm = Replicate(
    model="meta/meta-llama-3-8b-instruct",
    model_kwargs={"temperature": 0.1, "max_new_tokens": 100}
)

# Define possible report types and their respective questions
report_questions = {
    "experiment_analysis": [
        "What is the shot number?",
        "What specific signals are you analyzing?",
        "What time range are you considering?",
        "What anomalies or trends are you interested in?",
        "What conclusions have you drawn from the data?"
    ],
    "data_summary": [
        "What dataset should be summarized?",
        "What key metrics should be included?",
        "Should the summary focus on trends, outliers, or specific periods?",
        "What format should the report be in?"
    ],
    "error_analysis": [
        "Which system or experiment produced the errors?",
        "What type of errors are you analyzing?",
        "How frequently do these errors occur?",
        "What are the potential causes of these errors?",
        "What solutions have been proposed?"
    ]
}

# Dictionary to store user responses
user_responses = {}

def ask_llama(question):
    """Uses LLaMA-2 to generate responses based on user input."""
    response = llm.invoke(input=question)
    return response if isinstance(response, str) else "Could not generate a response."

def collect_responses(report_type):
    """Asks questions and stores responses for the selected report type."""
    user_responses["report_type"] = report_type
    for question in report_questions[report_type]:
        user_input = st.text_input(question, key=question)
        if user_input:
            user_responses[question] = user_input

def main():
    st.title("Report Generation Assistant")

    # Ask user for the type of report
    report_type = st.selectbox("What type of report do you want to create?", list(report_questions.keys()))

    if st.button("Start Report"):
        st.session_state["report_type"] = report_type

    if "report_type" in st.session_state:
        st.subheader(f"Generating {st.session_state['report_type']} Report")
        collect_responses(st.session_state["report_type"])

    if st.button("Finish and Generate Summary"):
        st.success("Report data collected successfully!")
        st.write("Summary of responses:")
        st.json(user_responses)  # Show collected responses in JSON format

        # Generate a textual summary using LLaMA
        summary_prompt = f"Summarize the following responses into a structured report:\n{user_responses}"
        summary = ask_llama(summary_prompt)
        st.subheader("Generated Report Summary")
        st.write(summary)

if __name__ == "__main__":
    main()