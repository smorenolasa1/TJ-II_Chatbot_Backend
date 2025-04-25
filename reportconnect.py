from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os, json, textwrap
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from docx import Document
from docx.shared import Pt, Inches
from dotenv import load_dotenv
import google.generativeai as genai

# Configuración inicial
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL_NAME = "models/gemini-1.5-pro"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

CONTEXT_DIR = "context"
STATIC_DIR = "static"
os.makedirs(CONTEXT_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

@app.get("/generate_report")
def generate_report():
    files = {
        "SimilPatternTool": "similpattern_history.json",
        "ShotLlama2": "shotllama2_history.json",
        "CsvUpdate": "csvupdate_history.json"
    }

    sections = []
    for section, file in files.items():
        path = os.path.join(CONTEXT_DIR, file)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                entries = json.load(f)
                if entries:
                    summary = f"### {section}\n"
                    for entry in entries:
                        summary += f"**Query:** {entry.get('question', '')}\n"
                        if "pattern_summary" in entry:
                            summary += f"**Pattern Summary:**\n{entry['pattern_summary']}\n"
                        if "response" in entry:
                            summary += f"**Results:**\n{entry['response']}\n"
                        if "plot_path" in entry:
                            summary += f"**Plot:** {entry['plot_path']}\n"
                        summary += "\n"
                    sections.append(summary)

    if not sections:
        return JSONResponse({"message": "No context to generate report."}, status_code=200)

    report_text = "# Plasma Fusion Tools Report\n\n" + "\n".join(sections)

    prompt = f"""
You are a scientific assistant generating a clean, structured report based on plasma fusion tools analysis.

Generate clear section headers (no #), concise bullet points if useful, and format numerical tables when needed.

DO NOT write meta-instructions like "Here's the report".

Structure it like this when possible:

Tool Name
Query: ...
Pattern Summary:
[Table]
Results: ...
Plot: [keep the relative plot path]

Here is the raw input:
{report_text}
"""

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    cleaned = response.text.strip()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"report_{timestamp}.pdf"
    docx_filename = f"report_{timestamp}.docx"
    pdf_path = os.path.join(STATIC_DIR, pdf_filename)
    docx_path = os.path.join(STATIC_DIR, docx_filename)

    # ➤ DOCX
    doc = Document()
    doc.add_heading("Fusion Data Analysis Report", 0)
    for block in cleaned.split("\n\n"):
        lines = block.strip().split("\n")
        if lines[0].lower().startswith("plot:"):
            plot_path = lines[0].split(":", 1)[1].strip()
            full_path = os.path.join(plot_path)
            if os.path.exists(full_path):
                doc.add_picture(full_path, width=Inches(5.5))
        else:
            for line in lines:
                doc.add_paragraph(line.strip(), style='Normal')
    doc.save(docx_path)

    # ➤ PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    text = c.beginText(50, 750)
    text.setFont("Helvetica", 12)

    for block in cleaned.split("\n\n"):
        for line in block.strip().split("\n"):
            if line.lower().startswith("plot:"):
                c.drawText(text)
                text = c.beginText(50, text.getY() - 20)
                plot_path = line.split(":", 1)[1].strip()
                full_path = os.path.join(plot_path)
                if os.path.exists(full_path):
                    c.drawImage(ImageReader(full_path), 50, text.getY() - 220, width=500, height=200)
                    text.moveCursor(0, -220)
            else:
                for wrapped in textwrap.wrap(line, width=90):
                    text.textLine(wrapped)
        text.textLine("")
        text.moveCursor(0, -10)
    c.drawText(text)
    c.save()

    print("✅ Returning report URLs:")
    print(f"PDF: http://localhost:5005/static/{pdf_filename}")
    print(f"Word: http://localhost:5005/static/{docx_filename}")

    return {
        "pdf_url": f"http://localhost:5005/static/{pdf_filename}",
        "word_url": f"http://localhost:5005/static/{docx_filename}"
    }

@app.post("/reset_context")
def reset_context():
    deleted = []
    for file in ["similpattern_history.json", "shotllama2_history.json", "csvupdate_history.json"]:
        path = os.path.join(CONTEXT_DIR, file)
        if os.path.exists(path):
            os.remove(path)
            deleted.append(file)
    return {"message": f"Deleted: {deleted}"}

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")