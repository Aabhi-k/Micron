import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import router as api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code executed on startup (Management)
    logger.info("Starting up backend service...")
    # TODO: Initialize Qdrant connection here
    # TODO: Initialize MCP client here
    yield
    # Code executed on shutdown
    logger.info("Shutting down backend service...")

# FastAPI Application Management
app = FastAPI(
    title="Legacy Code Documenter", 
    description="API for the AI Hackathon",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Management (Required for React frontend to talk to FastAPI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with frontend URL like "http://localhost:5173"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the endpoints from the separate api.py file
app.include_router(api_router, prefix="/api", tags=["Documentation"])

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    # Server management
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

