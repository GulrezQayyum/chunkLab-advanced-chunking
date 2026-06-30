# ChunkLab API

A learn-by-building RAG project. Each week adds a new chunking strategy.

## Setup

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your Grok API key
cp .env.example .env
# Open .env and paste your key from https://console.x.ai

# 4. Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Try it

Open http://localhost:8000/docs in your browser.
FastAPI gives you a free interactive UI to test every endpoint.

### Quick test flow:
1. POST /api/v1/upload  — upload any .txt or .pdf, strategy="fixed"
2. Copy the doc_id from the response
3. POST /api/v1/query   — paste doc_id, ask a question
4. GET  /api/v1/chunks/{doc_id} — inspect the raw chunks

## Project structure

```
chunklab/
├── app/
│   ├── main.py              # FastAPI app, CORS, routes
│   ├── vector_store.py      # ChromaDB + embeddings
│   ├── chunkers/
│   │   ├── __init__.py      # Strategy router (add new ones here)
│   │   ├── fixed_chunker.py         # Week 1 done
│   │   ├── parent_child_chunker.py  # Week 2 done
│   │   ├── semantic_chunker.py      # Week 3 (coming)
│   │   └── late_chunker.py          # Week 4 (coming)
│   └── routers/
│       └── documents.py     # /upload /query /chunks endpoints
├── requirements.txt
└── .env                     # your GROK_API_KEY (never commit this)
```

## Week-by-week plan

| Week | Strategy | What you learn |
|------|----------|----------------|
| 1 | Fixed-size chunking | RAG pipeline basics |
| 2 | Parent-child chunking | Why retrieval granularity ≠ context granularity |
| 3 | Semantic chunking | Embedding geometry, topic boundaries |
| 4 | Late chunking | Context-aware embeddings, global document understanding |
