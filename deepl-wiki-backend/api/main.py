"""FastAPI application for DeepL Wiki Backend API."""

import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Add the agents directory to the path
AGENTS_DIR = Path(__file__).parent.parent / "deepl-wiki-agents"
sys.path.insert(0, str(AGENTS_DIR))

# Load environment variables
load_dotenv()

from .routes import chat, repositories, files, health

app = FastAPI(
    title="DeepL Wiki API",
    description="Interactive documentation management system API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
app.include_router(repositories.router, prefix="/api/v1", tags=["repositories"])
app.include_router(files.router, prefix="/api/v1", tags=["files"])
app.include_router(health.router, prefix="/api/v1", tags=["health"])

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "DeepL Wiki API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
