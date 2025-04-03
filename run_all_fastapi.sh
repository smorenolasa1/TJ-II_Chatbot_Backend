#!/bin/bash

# Run all FastAPI servers in separate background processes

echo "🚀 Starting csvuploadconnect.py on port 5001"
uvicorn csvuploadconnect:app --host 0.0.0.0 --port 5001 --reload &

echo "🚀 Starting csvllama2connect.py on port 5002"
uvicorn csvllama2connect:app --host 0.0.0.0 --port 5002 --reload &

echo "🚀 Starting shotllama2connect.py on port 5003"
uvicorn shotllama2connect:app --host 0.0.0.0 --port 5003 --reload &

echo "🚀 Starting similpatternconnection.py on port 5004"
uvicorn similpatternconnection:app --host 0.0.0.0 --port 5004 --reload &

echo "✅ All FastAPI servers started!"