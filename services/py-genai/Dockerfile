# Use a modern, slim Python base image
FROM python:3.11-slim

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

# Copy the application source code
COPY src/ ./src

# Add the app directory to the Python path
ENV PYTHONPATH=/app

# Expose the port the app runs on
EXPOSE 8000

# Run the application with Uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
