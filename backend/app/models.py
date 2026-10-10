from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_name: str
    page_number: int
    excerpt: str | None = None


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=20)


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]


class UploadResponse(BaseModel):
    message: str
    indexed_documents: list[str]
    chunk_count: int


class ResetResponse(BaseModel):
    message: str
