#!/bin/bash
# Install spaCy model before starting FastAPI
python -m spacy download es_core_news_sm
uvicorn main:app --host 0.0.0.0 --port $PORT