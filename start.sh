#!/bin/bash

# Start the FastAPI backend in the background
echo "Starting FastAPI backend on port 8000..."
uvicorn app:app --host 0.0.0.0 --port 8000 &

# Wait briefly for backend to initialize
sleep 3

# Start the Streamlit frontend in the foreground on the assigned PORT (defaults to 8501)
echo "Starting Streamlit frontend on port ${PORT:-8501}..."
streamlit run streamlit_app.py --server.port ${PORT:-8501} --server.address 0.0.0.0
