from pathlib import Path
import sys

APP_DIR = Path(__file__).resolve().parent
VENV_SITE_PACKAGES = APP_DIR.parent / "venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"

if APP_DIR.as_posix() not in sys.path:
    sys.path.insert(0, APP_DIR.as_posix())

if VENV_SITE_PACKAGES.exists() and VENV_SITE_PACKAGES.as_posix() not in sys.path:
    sys.path.insert(0, VENV_SITE_PACKAGES.as_posix())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import chromadb

# Import routers
from routers.document2 import router as document_router, init_parent_child_retriever
from chunkers import ParentChildChunker, SemanticChunker

app = FastAPI(
    title="ChunkLab",
    version="0.3.0",
    description="Advanced RAG with Multiple Chunking Strategies"
)

# CORS for Flutter
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== Initialize ChromaDB (Persistent Storage) ==========
db_dir = APP_DIR / "chroma_data"
db_dir.mkdir(exist_ok=True)

chroma_client = chromadb.PersistentClient(path=str(db_dir))

# Load document once
meditations_path = APP_DIR / "meditations.txt"
doc_text = ""

try:
    with open(meditations_path, "r", encoding="utf-8") as f:
        doc_text = f.read()
    if not doc_text.strip():
        print("⚠️  meditations.txt is empty")
except FileNotFoundError:
    print(f"⚠️  meditations.txt not found at: {meditations_path}")
except Exception as e:
    print(f"❌ Error loading meditations: {str(e)}")

# ========== Initialize Parent-Child Chunking ==========
print("\n" + "="*60)
print("🔄 Initializing Parent-Child Chunking...")
print("="*60)

pc_collection = chroma_client.get_or_create_collection(
    name="meditations_parent_child",
    metadata={"hnsw:space": "cosine", "strategy": "parent_child"}
)

if pc_collection.count() == 0 and doc_text.strip():
    try:
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
        
        print(f"✅ Added {len(chunk_result['parents'])} parents + {len(chunk_result['children'])} children")
        
    except Exception as e:
        print(f"❌ Error initializing parent-child: {str(e)}")
else:
    print(f"✅ Collection already populated with {pc_collection.count()} chunks")

# ========== Initialize Semantic Chunking ==========
print("\n" + "="*60)
print("🧠 Initializing Semantic Chunking...")
print("="*60)

semantic_collection = chroma_client.get_or_create_collection(
    name="meditations_semantic",
    metadata={"hnsw:space": "cosine", "strategy": "semantic"}
)

if semantic_collection.count() == 0 and doc_text.strip():
    try:
        # Initialize semantic chunker with threshold=0.5 (moderate)
        semantic_chunker = SemanticChunker(similarity_threshold=0.5)
        semantic_chunks, metrics = semantic_chunker.chunk_with_metrics(doc_text)
        
        print(f"\n📊 Chunking Metrics:")
        print(f"   • Total chunks: {metrics.total_chunks}")
        print(f"   • Avg chunk size: {metrics.avg_chunk_size:.0f} words")
        print(f"   • Range: {metrics.min_chunk_size}-{metrics.max_chunk_size} words")
        print(f"   • Avg similarity: {metrics.avg_similarity_score:.3f}")
        
        # Add chunks to collection
        import hashlib
        doc_hash = hashlib.md5(doc_text.encode()).hexdigest()[:8]
        
        for idx, chunk in enumerate(semantic_chunks):
            chunk_id = f"meditations_{doc_hash}_semantic_{idx:03d}"
            semantic_collection.add(
                ids=[chunk_id],
                documents=[chunk],
                metadatas=[{
                    "strategy": "semantic",
                    "chunk_index": idx,
                    "total_chunks": len(semantic_chunks),
                    "word_count": len(chunk.split()),
                }]
            )
            
            if (idx + 1) % 10 == 0:
                print(f"   ✓ Added {idx + 1}/{len(semantic_chunks)} chunks")
        
        print(f"✅ Semantic chunking complete: {len(semantic_chunks)} chunks added")
        
    except ImportError:
        print("⚠️  SemanticChunker not available (sentence-transformers not installed)")
        print("   → Install: pip install sentence-transformers")
    except Exception as e:
        print(f"❌ Error initializing semantic chunking: {str(e)}")
else:
    print(f"✅ Collection already populated with {semantic_collection.count()} chunks")

# ========== Initialize Retriever & Router ==========
print("\n" + "="*60)
print("🔗 Setting up API Router...")
print("="*60)

app.include_router(document_router, prefix="/api/documents", tags=["Document Q&A"])
init_parent_child_retriever(chroma_client, "meditations_parent_child")

print("✅ API router initialized")

# ========== Health Checks ==========
@app.get("/health")
async def health():
    """Basic health check."""
    return {
        "status": "OK",
        "service": "ChunkLab",
        "version": "0.3.0",
    }

@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check with strategy info."""
    return {
        "status": "healthy",
        "service": "ChunkLab",
        "version": "0.3.0",
        "strategies": {
            "parent_child": {
                "available": True,
                "collection": "meditations_parent_child",
                "total_chunks": pc_collection.count(),
            },
            "semantic": {
                "available": semantic_collection.count() > 0,
                "collection": "meditations_semantic",
                "total_chunks": semantic_collection.count(),
            }
        }
    }

@app.get("/")
async def root():
    """Welcome endpoint."""
    return {
        "message": "🧠 ChunkLab - Advanced RAG with Multiple Chunking Strategies",
        "docs": "http://localhost:8001/docs",
        "available_endpoints": [
            "POST /api/documents/query?strategy=parent_child",
            "POST /api/documents/query?strategy=semantic",
            "GET /api/documents/health",
            "GET /api/documents/strategies",
            "GET /health",
            "GET /health/detailed",
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 Starting ChunkLab Server...")
    print("="*60)
    print("📍 Base URL: http://localhost:8001")
    print("📖 API Docs: http://localhost:8001/docs")
    print("✨ Try: POST /api/documents/query?strategy=semantic")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)