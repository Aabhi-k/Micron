import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code executed on startup
    logger.info("Starting up backend service...")
    yield
    # Code executed on shutdown
    logger.info("Shutting down backend service...")


app = FastAPI(
    title="Backend Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
