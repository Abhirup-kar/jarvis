# Multi-stage / Production-ready Dockerfile for JARVIS Assistant
FROM python:3.12-slim

# Prevent interactive prompts & buffer stdout
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1

# Install essential system dependencies (audio, video, OpenCV, OpenGL, ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    portaudio19-dev \
    libasound2-dev \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy source repository
COPY . /app/

# Create runtime directories
RUN mkdir -p storage/sqlite storage/vector_db storage/logs

# Expose HTTP and WebSocket ports
EXPOSE 8000 8765

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Start the JARVIS system
CMD ["python", "main.py"]

