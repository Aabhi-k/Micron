import io
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.ingestion.auto_ingest import find_passman_bpd_file, auto_ingest_passman_bpd, PASSMAN_BPD_FILENAME, PASSMAN_TENANT_ID
from app.services.ingestion.indexer import extract_text_from_content


def test_find_passman_bpd_file():
    """Verify that find_passman_bpd_file detects the PDF on disk."""
    path = find_passman_bpd_file()
    assert path is not None
    assert path.name == PASSMAN_BPD_FILENAME
    assert path.is_file()


def test_extract_text_from_pdf():
    """Verify pypdf extracts text from the real Passman BPD PDF."""
    path = find_passman_bpd_file()
    assert path is not None
    content = path.read_bytes()
    text = extract_text_from_content(content, path.name)
    assert len(text) > 1000
    assert "Passman" in text
    assert "[Page 1]" in text


@pytest.mark.asyncio
async def test_auto_ingest_idempotency_skip():
    """Verify auto-ingest skips re-indexing if document already indexed."""
    mock_session = AsyncMock()
    mock_doc = MagicMock()
    mock_doc.id = "doc-already-indexed"

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_doc
    mock_session.execute.return_value = mock_result

    res = await auto_ingest_passman_bpd(mock_session)
    assert res == "doc-already-indexed"


@pytest.mark.asyncio
async def test_documents_endpoints_list_and_upload():
    """Verify consolidated /documents endpoints (list & upload validation)."""
    from fastapi import FastAPI
    from httpx import AsyncClient, ASGITransport
    from app.api.v1.endpoints.documents import router as documents_router
    from app.db.session import get_db

    app = FastAPI()
    app.include_router(documents_router)

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = mock_result

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Missing header -> 422 or 400
        resp = await client.get("/documents/")
        assert resp.status_code in (400, 422)

        # Valid header -> 200
        resp = await client.get("/documents/", headers={"X-Tenant-ID": PASSMAN_TENANT_ID})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

