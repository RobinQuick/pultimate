"""Pultimate API - FastAPI with graceful import debugging."""

import sys
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Debug: Print path to help diagnose
print(f"Python path: {sys.path}")
print(f"Current file: {__file__}")

# Try imports one by one to identify the failing module
IMPORT_ERRORS = []
FULL_MODE = True

try:
    from core.config import settings

    print("✓ core.config imported")
except Exception as e:
    IMPORT_ERRORS.append(f"core.config: {e}")
    print(f"✗ core.config failed: {e}")
    traceback.print_exc()
    settings = type("obj", (object,), {"PROJECT_NAME": "Pultimate API"})()
    FULL_MODE = False

try:
    from database import init_db

    print("✓ database imported")
except Exception as e:
    IMPORT_ERRORS.append(f"database: {e}")
    print(f"✗ database failed: {e}")
    traceback.print_exc()

    async def init_db():
        pass

    FULL_MODE = False

try:
    from api.v1 import auth

    print("✓ api.v1.auth imported")
except Exception as e:
    IMPORT_ERRORS.append(f"api.v1.auth: {e}")
    print(f"✗ api.v1.auth failed: {e}")
    traceback.print_exc()
    auth = None
    FULL_MODE = False

try:
    from api.v1 import decks

    print("✓ api.v1.decks imported")
except Exception as e:
    IMPORT_ERRORS.append(f"api.v1.decks: {e}")
    print(f"✗ api.v1.decks failed: {e}")
    traceback.print_exc()
    decks = None
    FULL_MODE = False

try:
    from api.v1 import analysis

    print("✓ api.v1.analysis imported")
except Exception as e:
    IMPORT_ERRORS.append(f"api.v1.analysis: {e}")
    print(f"✗ api.v1.analysis failed: {e}")
    traceback.print_exc()
    analysis = None
    FULL_MODE = False

try:
    from api.v1 import templates

    print("✓ api.v1.templates imported")
except Exception as e:
    IMPORT_ERRORS.append(f"api.v1.templates: {e}")
    print(f"✗ api.v1.templates failed: {e}")
    traceback.print_exc()
    templates = None
    FULL_MODE = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    if FULL_MODE:
        try:
            await init_db()
        except Exception as e:
            print(f"Warning: Database initialization skipped: {e}")
    yield


app = FastAPI(title=getattr(settings, "PROJECT_NAME", "Pultimate API"), lifespan=lifespan, version="2.0.0")

# CORS configuration
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conditionally add routers
if auth:
    app.include_router(auth.router, prefix="/api/v1")
if decks:
    app.include_router(decks.router, prefix="/api/v1")
if analysis:
    app.include_router(analysis.router, prefix="/api/v1")
if templates:
    app.include_router(templates.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "2.0.0",
        "mode": "full" if FULL_MODE else "minimal",
        "import_errors": IMPORT_ERRORS if IMPORT_ERRORS else None,
    }


@app.get("/")
def root():
    return {"message": "Pultimate API is running", "mode": "full" if FULL_MODE else "minimal"}
