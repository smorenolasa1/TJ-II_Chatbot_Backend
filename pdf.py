import json
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def load_responses():
    """Loads saved responses from JSON file."""
    try:
        with open("user_responses.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("❌ No response file found. Make sure to complete the report first.")
        return {}

def generate_pdf(report_text):
    """Creates a well-formatted PDF file from the structured report."""
    try:
        pdf_file = "Generated_Report.pdf"
        c = canvas.Canvas(pdf_file, pagesize=letter)
        width, height = letter

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 50, "Generated Report")

        # Report Content
        c.setFont("Helvetica", 12)
        y_position = height - 80

        for line in report_text.split("\n"):
            if y_position < 50:  # If at bottom, create a new page
                c.showPage()
                c.setFont("Helvetica", 12)
                y_position = height - 50
            c.drawString(100, y_position, line)
            y_position -= 20

        c.save()
        print(f"✅ PDF successfully generated: {pdf_file}")
        return pdf_file

    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        return None

if __name__ == "__main__":
    # Load responses
    responses = load_responses()

    if not responses:
        print("❌ No responses found. Please complete the report first.")
        exit(1)  # Ensure subprocess detects failure

    try:
        # Generate structured report
        report_text = f"""
        {responses.get("report_type", "Unknown Report Type")} Report
        
        {json.dumps(responses, indent=2)}
        """

        # Generate the PDF
        pdf_path = generate_pdf(report_text)

        if pdf_path:
            print(f"✅ PDF Created: {pdf_path}")
            exit(0)  # Success
        else:
            print("❌ PDF generation failed.")
            exit(1)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        exit(1)  # Ensure subprocess detects failure