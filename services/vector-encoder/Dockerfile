FROM --platform=linux/amd64 python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy ONLY requirements first for better caching
COPY requirements.txt .

# Install Python dependencies in separate layer
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copy application code (this layer changes frequently)
COPY *.py .

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]