import os
import re
import uuid
import logging
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.services.embeddings import embedding_service

logger = logging.getLogger("backend.ingestion.legacy_indexer")

CODE_EXTENSIONS = {
    ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx",
    ".java", ".kt", ".scala",
    ".py", ".pyx",
    ".js", ".jsx", ".ts", ".tsx", ".mjs",
    ".go", ".rs", ".rb", ".php", ".swift",
    ".cs", ".vb",
    ".sql", ".sh", ".bash",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".mvn",
    "target", "build", "dist", ".venv", "venv",
}

def is_code_file(file_path: Path) -> bool:
    if any(part in SKIP_DIRS for part in file_path.parts):
        return False
    return file_path.suffix.lower() in CODE_EXTENSIONS

def get_authority_level(file_path: str) -> int:
    path_lower = file_path.lower()
    if "auth" in path_lower or "security" in path_lower or "jwt" in path_lower:
        return 3
    if "crypto" in path_lower or "encrypt" in path_lower or "password" in path_lower:
        return 3
    if "payment" in path_lower or "transaction" in path_lower:
        return 2
    return 1

def extract_metadata(file_path: str):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    pattern = re.compile(r'\b[\w\s\*\<\>\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{')
    functions = pattern.findall(content)

    lines = content.split('\n')
    header_text = '\n'.join(lines[:15])

    return functions, header_text

async def run_indexer():
    repo_dir = Path("/home/hb/code/mi/storage/projects")
    qdrant_client = QdrantClient(url="http://localhost:6333")
    collection_name = "codebase_index"

    if qdrant_client.collection_exists(collection_name=collection_name):
        qdrant_client.delete_collection(collection_name=collection_name)

    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
    )

    points = []
    indexed_count = 0
    skipped_count = 0

    if repo_dir.exists():
        for file_path in repo_dir.rglob("*"):
            if not file_path.is_file():
                continue

            if not is_code_file(file_path):
                skipped_count += 1
                continue

            file_name = file_path.name
            path_str = str(file_path)

            functions, header_text = extract_metadata(path_str)
            search_block = f"{file_name}\n{path_str}\n{', '.join(functions)}\n{header_text}"

            embedding, _ = await embedding_service.get_embedding(search_block)
            auth_level = get_authority_level(path_str)

            points.append(
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "file_path": path_str,
                        "file_name": file_name,
                        "functions": functions,
                        "minimum_authority_level": auth_level
                    }
                )
            )
            indexed_count += 1

        if points:
            qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )

    logger.info(f"Indexing complete: {indexed_count} code files indexed, {skipped_count} non-code files skipped.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_indexer())
