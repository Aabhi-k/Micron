import logging
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import Document
from app.services.ingestion.indexer import process_and_index_document
from app.core.config import settings

logger = logging.getLogger("backend.services.ingestion.auto_ingest")

PASSMAN_TENANT_ID = "00000000-0000-0000-0000-000000000001"
PASSMAN_PROJECT_ID = "passman-main"
PASSMAN_BPD_FILENAME = "Passman_BPD_Business_Process_Document.pdf"


def find_passman_bpd_file() -> Path | None:
    """Locates the Passman BPD PDF file across expected project storage locations."""
    candidates = [
        settings.STORAGE_BASE / "passman-main" / PASSMAN_BPD_FILENAME,
        Path("./storage/projects/passman-main") / PASSMAN_BPD_FILENAME,
        Path("../storage/projects/passman-main") / PASSMAN_BPD_FILENAME,
        Path(__file__).resolve().parent.parent.parent.parent.parent / "storage" / "projects" / "passman-main" / PASSMAN_BPD_FILENAME,
    ]
    for p in candidates:
        resolved = p.resolve()
        if resolved.is_file():
            return resolved
    return None


async def auto_ingest_passman_bpd(db: AsyncSession) -> str | None:
    """
    Idempotently ingests the Passman BPD document on application startup:
    1. Checks if Passman BPD is already indexed in PostgreSQL under project 'passman-main'.
    2. If already indexed, skips processing (0 startup overhead).
    3. If not, parses 21 pages via pypdf, chunks, embeds, and loads Qdrant and Postgres scoped to project.
    """
    pdf_path = find_passman_bpd_file()
    if not pdf_path:
        logger.info(f"Auto-ingest: '{PASSMAN_BPD_FILENAME}' not found on disk. Skipping.")
        return None

    # Check if already indexed under this project
    query = select(Document).where(
        Document.filename == PASSMAN_BPD_FILENAME,
        Document.status == "indexed"
    )
    result = await db.execute(query)
    existing_doc = result.scalars().first()

    if existing_doc:
        if not existing_doc.project_id:
            existing_doc.project_id = PASSMAN_PROJECT_ID
            await db.commit()
        logger.info(f"Auto-ingest: Passman BPD is already indexed (Document ID: {existing_doc.id}, Project: {existing_doc.project_id}). Skipping.")
        return str(existing_doc.id)

    logger.info(f"Auto-ingest: Found '{pdf_path.name}'. Starting automated BPD ingestion...")
    try:
        file_bytes = pdf_path.read_bytes()
        doc_id = await process_and_index_document(
            file_content=file_bytes,
            filename=PASSMAN_BPD_FILENAME,
            tenant_id_str=PASSMAN_TENANT_ID,
            db=db,
            project_id=PASSMAN_PROJECT_ID
        )
        if doc_id:
            logger.info(f"Auto-ingest: Successfully indexed Passman BPD (Document ID: {doc_id}) under tenant '{PASSMAN_TENANT_ID}' and project '{PASSMAN_PROJECT_ID}'.")
            return str(doc_id)
        else:
            logger.warning("Auto-ingest: Document processing returned None.")
            return None
    except Exception as e:
        logger.error(f"Auto-ingest error: {e}", exc_info=True)
        return None
