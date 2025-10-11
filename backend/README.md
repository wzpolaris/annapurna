# Backend (FastAPI)

This service exposes a small API that forwards chat prompts to OpenAI and returns the assistant response.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the repository root (or within `backend/`) with:

```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

## Run

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. Health check: `GET /health`, chat endpoint: `POST /chat`.
