#!/bin/bash

# Start FastAPI with only 1 worker to reduce memory usage
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1