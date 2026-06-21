from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import chromadb

# Import routers
from routers.document2 import router as document_router, init_parent_child_retriever
from chunkers import ParentChildChunker

app = FastAPI(title="ChunkLab")

# CORS for Flutter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== Initialize Parent-Child Chunking ==========
# CHANGE: Use persistent storage instead of in-memory
db_dir = Path(__file__).parent / "chroma_data"
db_dir.mkdir(exist_ok=True)

chroma_client = chromadb.PersistentClient(path=str(db_dir))
pc_collection = chroma_client.get_or_create_collection(
    name="meditations_parent_child",
    metadata={"hnsw:space": "cosine"}
)

# --- POPULATE THE COLLECTION (only if empty) ---
script_dir = Path(__file__).parent
meditations_path = script_dir / "meditations.txt"

if pc_collection.count() == 0:  # Only populate if empty
    try:
        with open(meditations_path, "r", encoding="utf-8") as f:
            doc_text = f.read()
        
        if doc_text.strip():
            chunker = ParentChildChunker(
                parent_chunk_size=1500,
                parent_overlap=200,
                child_chunk_size=400,
                child_overlap=50,
            )
            chunk_result = chunker.chunk(doc_text, doc_id="meditations_19d1ca3e")

            # Add parent chunks
            pc_collection.add(
                ids=[p.id for p in chunk_result['parents']],
                documents=[p.text for p in chunk_result['parents']],
                metadatas=[p.metadata for p in chunk_result['parents']],
            )
            
            # Add child chunks
            pc_collection.add(
                ids=[c.id for c in chunk_result['children']],
                documents=[c.text for c in chunk_result['children']],
                metadatas=[c.metadata for c in chunk_result['children']],
            )
            
            print(f"✅ Parent-Child Chunking: Added {len(chunk_result['parents'])} parents and {len(chunk_result['children'])} children to ChromaDB")
        else:
            print("⚠️  meditations.txt is empty")
            
    except FileNotFoundError:
        print(f"⚠️  meditations.txt not found at: {meditations_path}")
    except Exception as e:
        print(f"❌ Error loading meditations: {str(e)}")
else:
    print(f"✅ Database already populated with {pc_collection.count()} chunks")

# --- Initialize retriever ---
app.include_router(document_router, prefix="/api/documents", tags=["Document Q&A"])
init_parent_child_retriever(chroma_client, "meditations_parent_child")

# ========== Health Checks ==========
@app.get("/health")
async def health():
    return {"status": "OK", "service": "ChunkLab", "chunking": "parent-child"}

@app.get("/health/chunking")
async def health_chunking():
    return {
        "status": "active",
        "strategy": "parent-child",
        "collection": "meditations_parent_child",
        "total_chunks": pc_collection.count()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)