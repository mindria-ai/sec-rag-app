# Use a slim Python base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create app directory
WORKDIR /app

# Install system-level dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    poppler-utils \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app files
COPY . .

# Set Streamlit default config (optional)
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501

# Default command: run Streamlit app
CMD ["streamlit", "run", "main.py", "--server.runOnSave", "true", "--server.headless", "true", "--server.port", "8501"]
