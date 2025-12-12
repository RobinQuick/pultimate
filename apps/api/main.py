from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import jobs
import os

app = FastAPI(title="DeckLint API", version="1.0.0")

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://localhost",
    os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:3000"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
