import chromadb
from sentence_transformers import SentenceTransformer

# Load once at startup — this model runs 100% locally, no API key needed
# It converts text into a list of 384 numbers (an "embedding")
# Similar texts get similar numbers — that's how semantic search works
_model = SentenceTransformer("all-MiniLM-L6-v2")
_client = chromadb.PersistentClient(path="./chunklab_db")


def get_or_create_collection(doc_id: str, strategy: str):
    """Each document + strategy combo gets its own collection."""
    name = f"{doc_id}_{strategy}"
    return _client.get_or_create_collection(name)


def store_chunks(doc_id: str, strategy: str, chunks: list[dict]):
    """Embed and store chunks in ChromaDB."""
    collection = get_or_create_collection(doc_id, strategy)

    texts = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    # This is the core of RAG: turn text into vectors
    embeddings = _model.encode(texts).tolist()

    collection.add(
        documents=texts,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas,
    )
    return len(chunks)


def retrieve(doc_id: str, strategy: str, question: str, top_k: int = 4) -> list[str]:
    """
    Find the most relevant chunks for a question.
    This is semantic search: we embed the question and find chunks
    whose embeddings are closest in vector space.
    """
    collection = get_or_create_collection(doc_id, strategy)
    question_embedding = _model.encode([question]).tolist()

    results = collection.query(
        query_embeddings=question_embedding,
        n_results=min(top_k, collection.count()),
    )

    return results["documents"][0] if results["documents"] else []


def delete_collection(doc_id: str, strategy: str):
    name = f"{doc_id}_{strategy}"
    try:
        _client.delete_collection(name)
    except Exception:
        pass