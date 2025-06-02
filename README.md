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
MAC:
4. Launch all FastAPI servers:
   ```bash
   ./run_all_fastapi.sh
   ```

5. To stop all FastAPI servers:
   ```bash
   pkill -f "uvicorn"
   ```
WINDOWS:
4. Launch all FastAPI servers:
   ```bash
   .\run_all_fastapi.bat
5. Stop all FastAPI servers:
   ```bash
   taskkill /F /IM python.exe

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

# First Iteration Demos (Streamlit Development Phase)

During the early stages of the project, Streamlit was used to rapidly prototype and validate the backend functionalities before migrating to a dedicated frontend in React.  
Below are video demonstrations showcasing the progression of these initial iterations:

| Demo | Description | Link |
|:-----|:------------|:-----|
| Basic CSV Querying | User selects specific column names to clarify queries. | [View Demo](https://drive.google.com/file/d/1d-XmbU0FBs4v8vltmIZ6BGogoqoUWI-T/view?usp=sharing) |
| Simple Queries + Initial Graph Plotting | Basic questions and first iterations of signal plotting from CSV data. | [View Demo](https://drive.google.com/file/d/16VuyjFm1RLBzjVombza0IByjoRl-KsG3/view?usp=sharing) |
| Complex Queries + Pellet Dataset Integration | Extension to a second dataset (PelletInjections.csv) allowing more complex questions about pellet activity per discharge. | [View Demo](https://drive.google.com/file/d/1PRKRLAEUH3vJ2_EfZzS4N2tuaY-Ty1B5/view?usp=sharing) |
| LangChain CSV Agent with OpenAI | Streamlit prototype using `create_pandas_dataframe_agent` for uploading and querying CSVs. | [View Demo](https://drive.google.com/file/d/14DQc-aMyZuPqHDyI9S5ongd_6D-fPTwW/view?usp=drive_link) |