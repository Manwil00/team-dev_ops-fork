# Use Python 3.11 as base image
FROM python:3.11-slim

# Install system dependencies for vector databases and ML libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libblas-dev \
    liblapack-dev \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for faster builds
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY config/requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --only-binary=all -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create model cache directory for runtime model downloads
RUN mkdir -p /app/models && chmod 755 /app/models

# Set environment variables for model caching
ENV TRANSFORMERS_CACHE=/app/models
ENV SENTENCE_TRANSFORMERS_HOME=/app/models

# Set environment variables
ENV PYTHONPATH=/app
ENV TOKENIZERS_PARALLELISM=false

# Pre-download sentence transformer model for faster startup
RUN python3 src/download_model.py || echo "Model download failed, will download on first use"

EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
