#!/bin/bash
uvicorn csvllama2:app --host 0.0.0.0 --port 8000 & 
uvicorn pelletllama2:app --host 0.0.0.0 --port 8001