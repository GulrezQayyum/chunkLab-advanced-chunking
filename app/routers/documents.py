import os
import uuid
import fitz  # PyMuPDF — reads PDFs
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

from app.chunkers import get_chunker
from app.vector_store import store_chunks, retrieve, delete_collection

# Load environment variables
load_dotenv()

router = APIRouter()

# ── Groq client ─────────────────────────────────────────────
client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# ── Request / Response models ────────────────────────────────

class UploadResponse(BaseModel):
    doc_id: str
    strategy: str
    num_chunks: int
    preview: list[str]

class QueryRequest(BaseModel):
    doc_id: str
    question: str
    strategy: str = "fixed"

class QueryResponse(BaseModel):
    answer: str
    retrieved_chunks: list[str]
    strategy: str

class ChunksResponse(BaseModel):
    doc_id: str
    strategy: str
    chunks: list[dict]

# ── Helper: Extract text ────────────────────────────────────

def extract_text(file: UploadFile) -> str:
    content = file.file.read()

    if file.filename.endswith(".pdf"):
        doc = fitz.open(stream=content, filetype="pdf")
        return "\n".join(page.get_text() for page in doc)

    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1")

# ── Upload route ────────────────────────────────────────────

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    strategy: str = "fixed",
):
    text = extract_text(file)

    if not text.strip():
        raise HTTPException(400, "Could not extract text from file.")

    doc_id = str(uuid.uuid4())[:8]

    chunker = get_chunker(strategy)
    chunks = chunker.chunk(text)

    if not chunks:
        raise HTTPException(400, "Document produced no chunks.")

    delete_collection(doc_id, strategy)
    store_chunks(doc_id, strategy, chunks)

    return UploadResponse(
        doc_id=doc_id,
        strategy=strategy,
        num_chunks=len(chunks),
        preview=[c["text"][:200] for c in chunks[:3]],
    )

# ── Query route (RAG + Groq) ────────────────────────────────

@router.post("/query", response_model=QueryResponse)
async def query_document(body: QueryRequest):

    chunks = retrieve(body.doc_id, body.strategy, body.question)

    if not chunks:
        raise HTTPException(
            404,
            f"No chunks found for doc_id='{body.doc_id}'. Upload first."
        )

    context = "\n\n---\n\n".join(chunks)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. "
                    "Answer ONLY using the provided context. "
                    "If the answer is not in the context, say you don't know."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {body.question}",
            },
        ],
    )

    return QueryResponse(
        answer=response.choices[0].message.content,
        retrieved_chunks=chunks,
        strategy=body.strategy,
    )

# ── Get chunks ──────────────────────────────────────────────

@router.get("/chunks/{doc_id}", response_model=ChunksResponse)
async def get_chunks(doc_id: str, strategy: str = "fixed"):

    from app.vector_store import get_or_create_collection

    collection = get_or_create_collection(doc_id, strategy)
    results = collection.get(include=["documents", "metadatas"])

    chunks = [
        {"id": id_, "text": doc, "metadata": meta}
        for id_, doc, meta in zip(
            results["ids"],
            results["documents"],
            results["metadatas"],
        )
    ]

    return ChunksResponse(
        doc_id=doc_id,
        strategy=strategy,
        chunks=chunks,
    )