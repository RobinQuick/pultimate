FROM python:3.12-slim

# Install system dependencies
# libreoffice: for pptx -> pdf
# poppler-utils: for pdf -> png
# fonts-*: for better rendering fidelity
# libpq-dev: for postgres
# curl: for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    libreoffice \
    default-jre-headless \
    poppler-utils \
    fonts-liberation \
    fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Install python dependencies first (cached layer)
WORKDIR /app
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code to /app/apps/api
COPY apps/api/ /app/apps/api/

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set PYTHONPATH to the api package root
ENV PYTHONPATH=/app/apps/api
ENV PATH="/home/appuser/.local/bin:$PATH"

# Set WORKDIR to the api package
WORKDIR /app/apps/api

EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
