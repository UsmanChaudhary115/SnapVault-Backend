# Use official Python 3.10 slim image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Install necessary system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and model files
COPY . .

# Ensure model files are in the correct location
RUN mkdir -p /app/AI_Models/models/buffalo_l && \
    cp -r AI_Models/models/buffalo_l/* /app/AI_Models/models/buffalo_l/ || \
    echo "Warning: Model files not found in source directory"

# Expose default FastAPI port
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]