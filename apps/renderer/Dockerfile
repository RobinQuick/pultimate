FROM python:3.12-slim

WORKDIR /app

# Install LibreOffice and dependencies for headless rendering
# fonts-liberation and others for better font support
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libreoffice-headless \
    libreoffice-java-common \
    default-jre \
    fonts-liberation \
    fonts-dejavu \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
