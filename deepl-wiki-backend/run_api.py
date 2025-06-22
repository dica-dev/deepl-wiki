#!/usr/bin/env python3
"""Run the DeepL Wiki API server."""

import uvicorn
from api.main import app

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["api"]
    )
