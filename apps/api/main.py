"""Pultimate API - FastAPI Production App."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import analysis, auth, decks, templates
from core.config import settings
from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    try:
        await init_db()
    except Exception as e:
        print(f"Warning: Database initialization skipped: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
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

app.include_router(auth.router, prefix="/api/v1")
app.include_router(decks.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(templates.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0", "mode": "full"}


@app.get("/")
def root():
    return {"message": "Pultimate API is running", "mode": "full"}
