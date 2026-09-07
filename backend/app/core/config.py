import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Micron API"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database (PostgreSQL 16 + asyncpg)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/micron"
    )

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

    # Vector DB (Qdrant)
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "business_documents")

    # Embeddings & Search Pipeline
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    FALLBACK_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    RRF_K: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
