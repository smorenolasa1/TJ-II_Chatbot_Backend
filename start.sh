#!/bin/bash

# Install the spaCy model (if not already installed)
python -m spacy download es_core_news_sm

# Start FastAPI with only 1 worker to reduce memory usage
uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1