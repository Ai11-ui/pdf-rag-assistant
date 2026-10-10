# Deployment Guide: Vercel (Frontend) + Render (Backend)

## 1) Deploy FastAPI backend to Render

1. Create a new **Web Service** on Render using this repository.
2. Set **Root Directory** to `backend`.
3. Build command:
   ```bash
   pip install --upgrade pip && pip install .
   ```
4. Start command:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. Environment variables:
   - `FRONTEND_ORIGINS` (JSON list, include deployed Vercel URL)
   - `EMBEDDING_MODEL_NAME` (e.g. `sentence-transformers/all-MiniLM-L6-v2`)
   - `MAX_UPLOAD_SIZE_MB` (e.g. `15`)
   - `DEFAULT_TOP_K` (e.g. `4`)
   - `MAX_TOP_K` (e.g. `8`)

### Render storage note
The current FAISS index is stored in memory. Render's filesystem is ephemeral and service restarts clear in-memory state. Users need to re-upload PDFs after restart unless you add persistent external storage.

## 2) Deploy Next.js frontend to Vercel

1. Import this repository in Vercel.
2. Set **Root Directory** to `frontend`.
3. Framework preset should detect Next.js.
4. Configure environment variable:
   - `NEXT_PUBLIC_API_BASE_URL` = your Render backend URL (for example `https://your-backend.onrender.com`)
5. Deploy.

## 3) CORS and origin wiring

Add the final Vercel URL(s) to backend `FRONTEND_ORIGINS`, for example:

```text
["http://localhost:3000","https://your-app.vercel.app"]
```

If preview deployments are required, include preview domains too.
