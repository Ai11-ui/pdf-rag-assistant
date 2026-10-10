# PDF RAG Assistant

A full-stack PDF Retrieval-Augmented Generation (RAG) app with:

- **Frontend:** Next.js + TypeScript + Tailwind CSS
- **Backend:** FastAPI
- **Embeddings:** `sentence-transformers`
- **Vector search:** FAISS
- **Citations:** filename + page number + excerpt

## Repository layout

- `/frontend` – Next.js web application
- `/backend` – FastAPI API with PDF extraction, embedding, and retrieval
- `/docs/deployment-vercel-render.md` – deployment instructions

## Local setup

### Prerequisites

- Node.js 20+
- Python 3.11+

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

The frontend runs at `http://localhost:3000` and calls the backend at `NEXT_PUBLIC_API_BASE_URL`.

## Docker Compose (local)

```bash
docker compose up --build
```

## API overview

### `POST /api/upload`
Upload one or more PDF files (`files` form field), extract text with page metadata, chunk, embed, and index in FAISS.

Errors include:
- invalid file type
- file too large
- malformed PDF
- empty extraction

### `POST /api/chat`
Request body:

```json
{ "question": "What are the key findings?", "top_k": 4 }
```

Response includes:

- `answer`: generated response
- `citations`: array of `{ document_name, page_number, excerpt }`

### `POST /api/reset`
Clears the current in-memory index and chat context.

### `GET /health`
Health check endpoint.

## How generation works

The backend retrieves top passages with FAISS and `sentence-transformers` embeddings, then uses a deterministic **extractive fallback answerer**. This fallback ranks sentence overlap with question terms and returns grounded text from retrieved passages.

No external LLM API is required to get answers. If you later integrate an LLM, keep the same retrieval/citation flow.

## Environment variables

### Backend (`backend/.env`)
- `FRONTEND_ORIGINS` (JSON list of allowed origins)
- `EMBEDDING_MODEL_NAME`
- `MAX_UPLOAD_SIZE_MB`
- `DEFAULT_TOP_K`
- `MAX_TOP_K`

### Frontend (`frontend/.env.local`)
- `NEXT_PUBLIC_API_BASE_URL`

## Tests

Run backend tests:

```bash
cd backend
pytest
```

## Troubleshooting

- **422 malformed PDF / no extractable text:** ensure documents are valid, non-image-only PDFs.
- **404 on `/api/chat`:** upload PDFs first.
- **CORS errors:** add deployed frontend domains to `FRONTEND_ORIGINS`.
- **State disappears after restart/deploy:** current index is in-memory (ephemeral by design).
