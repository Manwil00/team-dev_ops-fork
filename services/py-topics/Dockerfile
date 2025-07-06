# ---- Builder Stage: To build dependencies ----
FROM python:3.11 as builder

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# We need build-essential for some dependencies of bertopic (e.g., hdbscan)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install uv

# Create a virtual environment
ENV VENV_PATH=/opt/venv
RUN python -m venv $VENV_PATH

# Activate virtual environment by adding it to the path
ENV PATH="$VENV_PATH/bin:$PATH"

# Copy requirements and install into the venv
WORKDIR /app
COPY requirements.txt ./
COPY generated ./generated
RUN uv pip install --no-cache -r requirements.txt \
    && uv pip install --no-cache --no-deps bertopic \
    && cd generated && uv pip install --no-cache .

# ---- Runtime Stage: The final, lean image ----
FROM python:3.11-slim

# Set environment variables for the runtime
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV VENV_PATH=/opt/venv
ENV PATH="$VENV_PATH/bin:$PATH"

# Create a non-root user to run the application for better security
RUN useradd --create-home appuser
USER appuser
WORKDIR /home/appuser

# Copy the virtual environment from the builder stage
COPY --from=builder $VENV_PATH $VENV_PATH

# Copy the application source code
COPY src ./src

# Expose the port and run the application
EXPOSE 8100
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8100"]
