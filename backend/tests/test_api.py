from fastapi.testclient import TestClient

from app.main import app, engine

client = TestClient(app)


def test_chat_requires_existing_index() -> None:
    engine.reset()
    response = client.post("/api/chat", json={"question": "What is this about?"})

    assert response.status_code == 404
    assert "Upload PDFs first" in response.json()["detail"]


def test_upload_rejects_non_pdf() -> None:
    engine.reset()
    response = client.post(
        "/api/upload",
        files={"files": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert "Upload PDF files only" in response.json()["detail"]


def test_chat_rejects_blank_question() -> None:
    response = client.post("/api/chat", json={"question": "   "})

    assert response.status_code == 422
