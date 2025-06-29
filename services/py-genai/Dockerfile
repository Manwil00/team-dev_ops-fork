# Use a modern, slim Python base image
FROM python:3.11-slim

# ACCEPT build-time arguments for Github Actions secrets.
ARG CHAIR_API_KEY
ARG GOOGLE_API_KEY

# 2. Update environment variables with the provided secrets
ENV CHAIR_API_KEY=${CHAIR_API_KEY}
ENV GOOGLE_API_KEY=${GOOGLE_API_KEY}

# Set environment variables for a clean, non-interactive environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install uv, the fast Python package installer
RUN pip install uv

# Copy only the requirements file to leverage Docker's layer caching
COPY requirements.txt ./

# Install dependencies using the much faster `uv`
# This replaces the slower `pip install`
RUN uv pip install --system --no-cache -r requirements.txt

# Copy and install the generated FastAPI models
COPY generated ./generated
RUN cd generated && uv pip install --system --no-cache . && cd ..

# Copy the application source code
COPY src/ ./src

# Add the app directory to the Python path
ENV PYTHONPATH=/app

# Expose the port the app runs on
EXPOSE 8000

# Run the application with Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
