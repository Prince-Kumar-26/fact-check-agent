FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for Playwright and other Python libraries
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright dependencies (chromium)
RUN playwright install chromium
RUN playwright install-deps

# Copy the rest of the application
COPY backend/ backend/
COPY alembic/ alembic/
COPY alembic.ini .

# Expose port
EXPOSE 8000

# Command to run
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000"]
