"""Pultimate API - FastAPI Production App."""
import os
import sys

# Ensure the app directory is in the path for local module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# Conditional imports - gracefully handle missing dependencies
try:
    from api.v1 import analysis, auth, decks, templates
    from core.config import settings
    from database import init_db
    FULL_MODE = True
except ImportError as e:
    print(f"Warning: Running in minimal mode due to import error: {e}")
    FULL_MODE = False
    settings = type('obj', (object,), {'PROJECT_NAME': 'Pultimate API'})()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if FULL_MODE:
        try:
            await init_db()
        except Exception as e:
            print(f"Warning: Database initialization skipped: {e}")
    yield


app = FastAPI(
    title=getattr(settings, 'PROJECT_NAME', 'Pultimate API'),
    lifespan=lifespan,
    version="2.0.0"
)

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://localhost",
    "*",  # Allow all for POC
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conditionally add routers
if FULL_MODE:
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(decks.router, prefix="/api/v1")
    app.include_router(analysis.router, prefix="/api/v1")
    app.include_router(templates.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0", "mode": "full" if FULL_MODE else "minimal"}


@app.get("/")
def root():
    return {"message": "Pultimate API is running", "mode": "full" if FULL_MODE else "minimal"}
