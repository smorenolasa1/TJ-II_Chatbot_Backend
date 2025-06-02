# Activar el entorno virtual
& "venv\Scripts\Activate.ps1"

# Lanzar todos los servidores FastAPI en segundo plano y mostrar logs
Start-Job { uvicorn csvuploadconnect:app --host 0.0.0.0 --port 5001 --reload }
Start-Job { uvicorn csvllama2connect:app --host 0.0.0.0 --port 5002 --reload }
Start-Job { uvicorn shotllama2connect:app --host 0.0.0.0 --port 5003 --reload }
Start-Job { uvicorn similpatternconnection:app --host 0.0.0.0 --port 5004 --reload }
Start-Job { uvicorn reportconnect:app --host 0.0.0.0 --port 5005 --reload }

Write-Host "✅ All FastAPI servers started!"