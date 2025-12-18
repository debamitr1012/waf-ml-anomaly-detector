FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY dashboard/ ./dashboard/
COPY config/ ./config/
COPY models/ ./models/
COPY scripts/ ./scripts/

# Create logs directory
RUN mkdir -p logs

# Expose ports
EXPOSE 8000 5000

# Default command (can be overridden)
CMD ["python", "src/main.py"]
