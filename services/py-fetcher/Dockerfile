FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install minimal deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy and install the generated FastAPI models
COPY generated ./generated
RUN cd generated && pip install --no-cache-dir . && cd ..

# Copy source code
COPY src ./src

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8200"]
