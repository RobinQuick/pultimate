"""Minimal FastAPI app for testing Fly.io deployment."""
from fastapi import FastAPI

app = FastAPI(title="Pultimate API", version="2.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}

@app.get("/")
def root():
    return {"message": "Pultimate API is running"}
