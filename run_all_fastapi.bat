@echo off
call venv\Scripts\activate

echo 🚀 Starting csvuploadconnect.py on port 5001
start /b "" uvicorn csvuploadconnect:app --host 0.0.0.0 --port 5001 --reload

echo 🚀 Starting csvllama2connect.py on port 5002
start /b "" uvicorn csvllama2connect:app --host 0.0.0.0 --port 5002 --reload

echo 🚀 Starting shotllama2connect.py on port 5003
start /b "" uvicorn shotllama2connect:app --host 0.0.0.0 --port 5003 --reload

echo 🚀 Starting similpatternconnection.py on port 5004
start /b "" uvicorn similpatternconnection:app --host 0.0.0.0 --port 5004 --reload

echo 📝 Starting reportconnect.py on port 5005
start /b "" uvicorn reportconnect:app --host 0.0.0.0 --port 5005 --reload

echo ✅ All FastAPI servers started!
pause