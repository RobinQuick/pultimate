FROM python:3.12-slim

WORKDIR /app

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

# Install python dependencies
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY apps/api/ .

# Set ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment path adjustment
ENV PYTHONPATH=/app
ENV PATH="/home/appuser/.local/bin:$PATH"

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (overridden in docker-compose/render.yaml)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
