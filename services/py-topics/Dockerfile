FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt ./ 
COPY generated ./generated

# 1. Install build-essential
# 2. Install uv for fast package management
# 3. Install Python dependencies using uv
# 4. Install generated FastAPI models
# 5. Clean up build-essential and apt cache
RUN apt-get update && apt-get install -y build-essential \
    && pip install uv \
    && uv pip install --system --no-cache -r requirements.txt \
    && cd generated && uv pip install --system --no-cache . && cd .. \ 
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY src ./src

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8100"]
