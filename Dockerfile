FROM python:3.11-slim

WORKDIR /app

# Install basic build tools and utility packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose Hugging Face's default web port
EXPOSE 7860

# Point Streamlit to the background FastAPI server on localhost
ENV RAG_API_URL=http://localhost:8000

# Make the startup script executable
RUN chmod +x start.sh

# Execute the startup script to start both servers
CMD ["./start.sh"]
