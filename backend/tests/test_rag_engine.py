import numpy as np

from app.services.pdf_processing import ChunkMetadata, DocumentChunk
from app.services.rag_engine import RagEngine


class FakeEmbedder:
    def encode(self, texts: list[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            text_lower = text.lower()
            vectors.append(
                [
                    float("cats" in text_lower),
                    float("dogs" in text_lower),
                    float("citations" in text_lower),
                ]
            )
        return np.array(vectors, dtype="float32")


def test_retrieve_and_answer_returns_citations() -> None:
    engine = RagEngine(model_name="unused")
    engine.embedder = FakeEmbedder()
    engine.add_chunks(
        [
            DocumentChunk("Cats are agile animals.", ChunkMetadata("pets.pdf", 1)),
            DocumentChunk("Dogs are loyal companions.", ChunkMetadata("pets.pdf", 2)),
        ]
    )

    answer, citations = engine.answer("What does the document say about cats?", top_k=1)

    assert "Cats" in answer
    assert len(citations) == 1
    assert citations[0].document_name == "pets.pdf"
    assert citations[0].page_number == 1
