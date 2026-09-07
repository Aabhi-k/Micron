import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Micron API"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Storage paths
    STORAGE_BASE: Path = Path(os.getenv("STORAGE_BASE", "./storage/projects")).resolve()
    VECTOR_STORE_DIR: Path = Path(os.getenv("VECTOR_STORE_DIR", "./vector_store")).resolve()

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"
    ]

    # MCP Server configuration
    MCP_SERVER_COMMAND: str = os.getenv("MCP_SERVER_COMMAND", "python")
    MCP_SERVER_ARGS: List[str] = ["-m", "mcp_server.server"]

    # Vector DB (Qdrant / Chroma)
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # LLM & Embedding Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
