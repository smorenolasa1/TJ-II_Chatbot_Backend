# Plasma Fusion Tools Backend

## Description

This backend is composed of several FastAPI microservices that support the frontend functionalities, including CSV querying, TJ-II data plotting, similarity pattern extraction, and automated report generation.  
The backend also connects to an external **SimilPatternTool** server running locally on port 8080.

---

## Requirements

- Python 3.8+
- pip (Python package manager)
- Java (for SimilPatternTool server)
- Google Generative AI API key (`GOOGLE_API_KEY`)
- Replicate API key (`REPLICATE_API_TOKEN`)

---

## Setup and Execution

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install additional SpaCy model for Spanish language processing:
   ```bash
   python -m spacy download es_core_news_sm
   ```

3. Make the script executable (only once):
   ```bash
   chmod +x run_all_fastapi.sh
   ```

4. Launch all FastAPI servers:
   ```bash
   ./run_all_fastapi.sh
   ```

5. To stop all FastAPI servers:
   ```bash
   pkill -f "uvicorn"
   ```

---

## Running the SimilPatternTool Server (localhost:8080)

The application connects to a local instance of **SimilPatternTool** running via two Java `.jar` files (client and server).

### 1. Create convenient aliases (optional but recommended)

Edit your terminal configuration file (example for `zsh`):
```bash
nano ~/.zshrc
```

Add the following lines:
```bash
alias client="java -jar -noverify /path/to/similarwave.jar"
alias server="java -jar /path/to/similPatternTool.jar"
```

Replace `/path/to/` with the correct paths to your `.jar` files.

Apply the changes:
```bash
source ~/.zshrc
```

Now you can easily start the client and server with:

```bash
client
server
```

Make sure the server is running on `localhost:8080` before using the frontend features related to similarity extraction.

---

## Backend Microservices Overview

| Microservice | Description | Port |
|:-------------|:-------------|:-----|
| csvllama2connect.py | Upload and query CSV files with AI assistance | 5001 |
| loadcsvconnect.py | Query uploaded CSV data (separate flow) | 5002 |
| shotllama2connect.py | Fetch TJ-II plots from the info.fusion.ciemat.es portal | 5003 |
| similpatternconnection.py | Similarity search and AI explanation with plots | 5004 |
| reportconnect.py | Generate full PDF and Word reports from analysis sessions | 5005 |

Each service runs independently via `uvicorn`.

---

## Important Notes

- `.env` files must be properly configured with valid API keys.
- Ensure ports `5001-5005` are free and not occupied by other applications.
- The SimilPatternTool server must be running to enable pattern similarity features.
- The backend uses CORS to allow requests from the frontend.

---

## Dependencies

- **FastAPI** (API framework)
- **Uvicorn** (ASGI server)
- **Pandas** (CSV processing)
- **Matplotlib** (Plot generation)
- **Google Generative AI (Gemini)**
- **Replicate API (LLaMA-2)**
- **SpaCy** (Natural Language Processing)
- **python-docx** (Word document generation)
- **ReportLab** (PDF generation)

---