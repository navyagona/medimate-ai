# Production Dockerfile for MediMate AI
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (for potential C-extensions/healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first to leverage Docker caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend and frontend source files
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Set working directory to backend for execution
WORKDIR /app/backend

# Expose FastAPI production port
EXPOSE 8000

# Environment variables configuration
ENV PORT=8000
ENV LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1

# Command to start the application using Uvicorn production server
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
