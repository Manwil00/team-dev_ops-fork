FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install uv for fast package management
RUN pip install uv

# Install dependencies
COPY requirements.txt ./
RUN uv pip install --system --no-cache -r requirements.txt

# Copy and install the generated FastAPI models
COPY generated ./generated
RUN cd generated && uv pip install --system --no-cache . && cd ..

# Copy source code
COPY src ./src

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8100"]
