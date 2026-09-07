from app.services.ingestion.chunker import chunk_text
from fastapi.testclient import TestClient

def test_chunk_text():
    sample_text = "A" * 5000
    chunks = chunk_text(sample_text)
    assert len(chunks) > 0
    assert len(chunks[0]) == 2000
    assert len(chunks[1]) == 2000
    assert "A" in chunks[0]

def test_upload_missing_tenant():
    from app.main import app
    client = TestClient(app)
    response = client.post("/api/v1/documents/upload", files={"file": ("test.txt", b"hello world")})
    assert response.status_code in (400, 422)
