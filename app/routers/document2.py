"""
Document Q&A with Parent-Child Chunking Strategy
- Child chunks: retrieved from vector DB (small, efficient)
- Parent chunks: returned to LLM (large, contextual)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

from chunkers import ParentChildRetriever


# ============================================================================
# Request/Response Models
# ============================================================================

class RetrievedChunk(BaseModel):
    chunk_id: str
    text: str
    similarity_score: float
    chunk_type: str
    parent_context: Optional[Dict] = None
    metadata: Dict


class QueryResponse(BaseModel):
    query: str
    results: List[RetrievedChunk]
    strategy: str
    timestamp: str


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter()

# Global state
_parent_child_retriever = None


def init_parent_child_retriever(chroma_client, collection_name: str):
    """Initialize the parent-child retriever (call from main.py)"""
    global _parent_child_retriever
    _parent_child_retriever = ParentChildRetriever(chroma_client, collection_name)


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/query", response_model=QueryResponse)
async def query_documents(
    query: str,
    n_results: int = 5,
    return_parents: bool = True,
):
    """
    Query documents using parent-child chunking strategy
    
    Request:
        {
            "query": "What is virtue?",
            "n_results": 5,
            "return_parents": true
        }
    
    Response:
        {
            "query": "What is virtue?",
            "results": [
                {
                    "chunk_id": "...",
                    "text": "... retrieved child chunk ...",
                    "similarity_score": 0.87,
                    "chunk_type": "child_with_parent",
                    "parent_context": {
                        "text": "... full parent chunk ...",
                        "metadata": {...}
                    }
                }
            ],
            "strategy": "child_chunks_with_parent_context",
            "timestamp": "2026-06-20T..."
        }
    """
    if not _parent_child_retriever:
        raise HTTPException(
            status_code=500,
            detail="Parent-child retriever not initialized. Check main.py setup."
        )

    try:
        retrieved = _parent_child_retriever.retrieve(
            query=query,
            n_results=n_results,
            return_parents=return_parents,
        )

        results = [
            RetrievedChunk(
                chunk_id=r['chunk_id'],
                text=r['text'],
                similarity_score=r['similarity_score'],
                chunk_type=r['chunk_type'],
                parent_context=r.get('parent_context'),
                metadata=r['metadata'],
            )
            for r in retrieved
        ]

        return QueryResponse(
            query=query,
            results=results,
            strategy='parent_chunks_with_context' if return_parents else 'child_chunks_only',
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_config():
    """Get current chunking configuration"""
    return {
        'strategy': 'parent_child',
        'description': 'Child chunks retrieved, parent chunks returned for context',
        'parent_chunk_size': 1500,
        'child_chunk_size': 400,
    }


@router.get("/stats")
async def get_stats():
    """Get collection statistics"""
    if not _parent_child_retriever:
        raise HTTPException(status_code=500, detail="Retriever not initialized")
    
    try:
        collection = _parent_child_retriever.collection
        count = collection.count()
        return {
            'total_chunks': count,
            'collection': 'meditations_parent_child',
            'status': 'active'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))