from collections.abc import Iterable
from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfReader


@dataclass(slots=True)
class ChunkMetadata:
    document_name: str
    page_number: int


@dataclass(slots=True)
class DocumentChunk:
    text: str
    metadata: ChunkMetadata


def split_text(text: str, chunk_size: int = 900, overlap: int = 120) -> Iterable[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + chunk_size)
        chunks.append(cleaned[start:end].strip())
        if end >= len(cleaned):
            break
        start = max(end - overlap, start + 1)
    return chunks


def extract_pdf_chunks(file_name: str, content: bytes) -> list[DocumentChunk]:
    reader = PdfReader(BytesIO(content))
    chunks: list[DocumentChunk] = []

    for index, page in enumerate(reader.pages):
        page_number = index + 1
        page_text = (page.extract_text() or "").strip()
        for chunk in split_text(page_text):
            chunks.append(
                DocumentChunk(
                    text=chunk,
                    metadata=ChunkMetadata(document_name=file_name, page_number=page_number),
                )
            )
    return chunks
