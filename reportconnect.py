from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime
import os, json, textwrap
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from docx import Document
from docx.shared import Pt
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL_NAME = "models/gemini-1.5-pro"


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # O restringe según dominio en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
CONTEXT_DIR = "context"
STATIC_DIR = "static"
os.makedirs(CONTEXT_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

def clean_ai_response(text):
    return text.strip()

@app.get("/generate_report")
def generate_report():
    files = {
        "SimilPatternTool": "similpattern_history.json",
        "ShotLlama2": "shotllama2_history.json",
        "CsvUpdate": "csvupdate_history.json"
    }

    report_sections = []
    for section_name, filename in files.items():
        path = os.path.join(CONTEXT_DIR, filename)
        if not os.path.exists(path):
            continue

        with open(path, "r", encoding="utf-8") as f:
            entries = json.load(f)

        if not entries:
            continue

        section_text = f"{section_name}:\n"
        for i, entry in enumerate(entries):
            section_text += f"\nQuestion {i+1}: {entry.get('question', '')}\n"
            if "pattern_summary" in entry and entry["pattern_summary"]:
                section_text += f"Pattern Summary:\n{entry['pattern_summary']}\n"
            if "response" in entry and entry["response"]:
                section_text += f"AI Response:\n{entry['response']}\n"
            if "plot_path" in entry and entry["plot_path"]:
                section_text += f"Plot Path: {entry['plot_path']}\n"

        report_sections.append(section_text)

    if not report_sections:
        return JSONResponse({"message": "No context to generate report."}, status_code=200)

    combined_report = "\n\n".join(report_sections)
    prompt = f"""
    You are a scientific assistant generating a structured report based on plasma fusion tools.
    Write a well-formatted report with clear sections, and no extra commentary or formatting hints.

    {combined_report}
    """

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    cleaned = clean_ai_response(response.text)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_filename = f"report_{timestamp}.pdf"
    docx_filename = f"report_{timestamp}.docx"
    pdf_path = os.path.join(STATIC_DIR, pdf_filename)
    docx_path = os.path.join(STATIC_DIR, docx_filename)

    # PDF
    c = canvas.Canvas(pdf_path, pagesize=letter)
    text = c.beginText(40, 750)
    text.setFont("Helvetica", 11)
    for line in cleaned.split("\n"):
        for wrap in textwrap.wrap(line, width=90):
            text.textLine(wrap)
    c.drawText(text)
    c.showPage()
    c.save()

    # DOCX
    doc = Document()
    doc.add_heading("Fusion Analysis Report", 0)
    for paragraph in cleaned.split("\n\n"):
        p = doc.add_paragraph(paragraph.strip())
        p.style.font.size = Pt(11)
    doc.save(docx_path)
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

app.mount("/static", StaticFiles(directory="static"), name="static")