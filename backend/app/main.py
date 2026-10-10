from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pypdf.errors import PdfReadError

from app.config import get_settings
from app.models import ChatRequest, ChatResponse, ResetResponse, UploadResponse
from app.services.pdf_processing import extract_pdf_chunks
from app.services.rag_engine import RagEngine

settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = RagEngine(model_name=settings.embedding_model_name, default_top_k=settings.default_top_k)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/upload", response_model=UploadResponse)
async def upload(files: list[UploadFile] = File(...)) -> UploadResponse:
    if not files:
        raise HTTPException(status_code=400, detail="At least one PDF file is required.")

    indexed_documents: list[str] = []
    all_chunks = []
    size_limit = settings.max_upload_size_mb * 1024 * 1024

    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Each uploaded file must have a name.")
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"Unsupported file type for '{file.filename}'. Upload PDF files only.")

        content = await file.read()
        if len(content) > size_limit:
            raise HTTPException(
                status_code=413,
                detail=f"File '{file.filename}' exceeds the {settings.max_upload_size_mb}MB size limit.",
            )

        try:
            chunks = extract_pdf_chunks(file_name=file.filename, content=content)
        except PdfReadError as exc:
            raise HTTPException(status_code=422, detail=f"File '{file.filename}' is not a valid PDF.") from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=422, detail=f"Failed to process '{file.filename}'.") from exc

        if not chunks:
            raise HTTPException(status_code=422, detail=f"No extractable text found in '{file.filename}'.")

        indexed_documents.append(file.filename)
        all_chunks.extend(chunks)

    engine.reset()
    engine.add_chunks(all_chunks)

    return UploadResponse(
        message="PDFs uploaded and indexed successfully.",
        indexed_documents=indexed_documents,
        chunk_count=len(all_chunks),
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question must not be empty.")
    if not engine.has_index():
        raise HTTPException(status_code=404, detail="No indexed documents available. Upload PDFs first.")

    requested_top_k = payload.top_k or settings.default_top_k
    top_k = min(requested_top_k, settings.max_top_k)
    answer, citations = engine.answer(question=question, top_k=top_k)
    return ChatResponse(answer=answer, citations=citations)


@app.post("/api/reset", response_model=ResetResponse)
def reset() -> ResetResponse:
    engine.reset()
    return ResetResponse(message="Session reset. Upload new PDFs to start over.")
