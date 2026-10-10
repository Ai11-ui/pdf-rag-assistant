from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from app.services.pdf_processing import extract_pdf_chunks


def make_pdf() -> bytes:
    buffer = BytesIO()
    doc = canvas.Canvas(buffer, pagesize=letter)
    doc.drawString(100, 700, "First page includes an overview of RAG retrieval.")
    doc.showPage()
    doc.drawString(100, 700, "Second page describes citations with page numbers.")
    doc.save()
    return buffer.getvalue()


def test_extract_pdf_chunks_preserves_page_metadata() -> None:
    chunks = extract_pdf_chunks("sample.pdf", make_pdf())

    assert chunks
    page_numbers = {chunk.metadata.page_number for chunk in chunks}
    document_names = {chunk.metadata.document_name for chunk in chunks}

    assert page_numbers == {1, 2}
    assert document_names == {"sample.pdf"}
