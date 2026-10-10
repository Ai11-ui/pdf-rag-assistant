from __future__ import annotations

import re
from dataclasses import dataclass
from hashlib import sha256

import faiss
import numpy as np

from app.models import Citation
from app.services.pdf_processing import DocumentChunk


@dataclass(slots=True)
class RetrievalResult:
    chunk: DocumentChunk
    score: float


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None
        self._use_fallback = False

    def _load_model(self):
        if self._use_fallback:
            return None
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except Exception:  # noqa: BLE001
                self._use_fallback = True
                return None

            try:
                self._model = SentenceTransformer(self.model_name)
            except Exception:  # noqa: BLE001
                self._use_fallback = True
                return None
        return self._model

    def _fallback_encode(self, texts: list[str], dimensions: int = 384) -> np.ndarray:
        vectors = np.zeros((len(texts), dimensions), dtype="float32")
        for row, text in enumerate(texts):
            for term in re.findall(r"\w+", text.lower()):
                digest = sha256(term.encode("utf-8")).hexdigest()
                bucket = int(digest, 16) % dimensions
                vectors[row, bucket] += 1.0
        return vectors

    def encode(self, texts: list[str]) -> np.ndarray:
        model = self._load_model()
        if model is None:
            embeddings = self._fallback_encode(texts)
            return embeddings.astype("float32")
        embeddings = model.encode(texts, convert_to_numpy=True)
        return embeddings.astype("float32")


class RagEngine:
    def __init__(self, model_name: str, default_top_k: int = 4) -> None:
        self.default_top_k = default_top_k
        self.embedder = SentenceTransformerEmbedder(model_name=model_name)
        self.reset()

    def reset(self) -> None:
        self._chunks: list[DocumentChunk] = []
        self._index: faiss.Index | None = None

    def has_index(self) -> bool:
        return self._index is not None and len(self._chunks) > 0

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            return

        embeddings = self.embedder.encode([chunk.text for chunk in chunks])
        faiss.normalize_L2(embeddings)

        if self._index is None:
            self._index = faiss.IndexFlatIP(embeddings.shape[1])

        self._index.add(embeddings)
        self._chunks.extend(chunks)

    def retrieve(self, question: str, top_k: int | None = None) -> list[RetrievalResult]:
        if not self.has_index() or self._index is None:
            return []

        requested_top_k = top_k or self.default_top_k
        search_k = max(1, min(requested_top_k, len(self._chunks)))

        query_embedding = self.embedder.encode([question])
        faiss.normalize_L2(query_embedding)
        scores, indices = self._index.search(query_embedding, search_k)

        results: list[RetrievalResult] = []
        for raw_score, idx in zip(scores[0], indices[0], strict=True):
            if idx < 0:
                continue
            results.append(RetrievalResult(chunk=self._chunks[idx], score=float(raw_score)))
        return results

    def _extractive_answer(self, question: str, passages: list[RetrievalResult]) -> str:
        query_terms = {term.lower() for term in re.findall(r"\w+", question) if len(term) > 2}
        if not query_terms:
            return " ".join(result.chunk.text for result in passages[:2])

        sentence_candidates: list[tuple[int, str]] = []
        for result in passages:
            for sentence in re.split(r"(?<=[.!?])\s+", result.chunk.text):
                sentence_terms = {term.lower() for term in re.findall(r"\w+", sentence)}
                overlap = len(query_terms.intersection(sentence_terms))
                if overlap > 0:
                    sentence_candidates.append((overlap, sentence.strip()))

        if not sentence_candidates:
            return "I couldn't find an exact match, but the most relevant passages are: " + " ".join(
                result.chunk.text for result in passages[:2]
            )

        sentence_candidates.sort(key=lambda item: item[0], reverse=True)
        top_sentences = [sentence for _, sentence in sentence_candidates[:3]]
        return " ".join(top_sentences)

    def answer(self, question: str, top_k: int | None = None) -> tuple[str, list[Citation]]:
        retrieved = self.retrieve(question=question, top_k=top_k)
        if not retrieved:
            return "No indexed content is available yet. Upload PDFs to begin.", []

        answer = self._extractive_answer(question=question, passages=retrieved)
        citations: list[Citation] = []
        for result in retrieved:
            citations.append(
                Citation(
                    document_name=result.chunk.metadata.document_name,
                    page_number=result.chunk.metadata.page_number,
                    excerpt=result.chunk.text[:220],
                )
            )
        return answer, citations
