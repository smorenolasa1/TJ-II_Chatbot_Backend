import os
import json
from langchain_community.llms import Replicate
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from report import user_responses  # Import responses directly from report.py

# Load environment variables
load_dotenv()
os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")

# Set up Replicate LLaMA-2
llm = Replicate(
    model="meta/meta-llama-3-8b-instruct",
    model_kwargs={"temperature": 0.1, "max_new_tokens": 500}
)

def generate_report_text(user_responses):
    """Uses LLaMA to generate a structured report based on user responses."""
    prompt = (
        "You are a professional assistant. Structure the following user responses into a well-organized report:\n"
        f"{json.dumps(user_responses, indent=2)}\n"
        "The report should have an Introduction, Analysis, and Conclusions section. Format it clearly."
    )
    structured_report = llm.invoke(input=prompt)
    return structured_report if isinstance(structured_report, str) else "Could not generate a structured report."

def create_pdf(report_text, filename="Generated_Report.pdf"):
    """Creates a PDF file with the structured report."""
    pdf_file = filename
    c = canvas.Canvas(pdf_file, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 50, "Generated Report")

    # Report Content
    c.setFont("Helvetica", 12)
    text = c.beginText(100, height - 80)
    text.setFont("Helvetica", 12)

    # Add report text to PDF
    for line in report_text.split("\n"):
        text.textLine(line)

    c.drawText(text)
    c.save()
    print(f"PDF saved as {pdf_file}")

if __name__ == "__main__":
    if not user_responses:
        print("No responses found from report.py. Please complete the report first.")
    else:
        report_text = generate_report_text(user_responses)
        create_pdf(report_text)
        print("Report successfully generated as a PDF.")