"""
Updated FastAPI router for ChunkLab RAG queries.
Supports multiple chunking strategies: fixed_size, parent_child, semantic

Usage:
    from fastapi import FastAPI
    from document2_semantic import router
    
    app = FastAPI()
    app.include_router(router)
    
Test in Swagger:
    http://localhost:8001/docs
    
Example queries:
    - POST /api/documents/query?strategy=semantic
    - POST /api/documents/query?strategy=parent_child
    - POST /api/documents/query?strategy=fixed_size
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import chromadb
from enum import Enum

# Initialize ChromaDB client
client = chromadb.Client()

router = APIRouter(prefix="/api/documents", tags=["documents"])


class ChunkingStrategy(str, Enum):
    """Supported chunking strategies."""
    FIXED_SIZE = "fixed_size"
    PARENT_CHILD = "parent_child"
    SEMANTIC = "semantic"
    HIERARCHICAL = "hierarchical"  # For future


class QueryRequest(BaseModel):
    """Request body for document queries."""
    query: str
    n_results: int = 5
    return_parents: bool = True


class ChunkResult(BaseModel):
    """A single chunk result."""
    id: str
    text: str
    similarity: float
    metadata: dict


class QueryResponse(BaseModel):
    """Response with query results."""
    strategy: str
    query: str
    results: List[ChunkResult]
    total_results: int
    metrics: Optional[dict] = None


def get_collection_name(strategy: ChunkingStrategy) -> str:
    """Map strategy enum to ChromaDB collection name."""
    mapping = {
        ChunkingStrategy.FIXED_SIZE: "meditations_fixed_size",
        ChunkingStrategy.PARENT_CHILD: "meditations_parent_child",
        ChunkingStrategy.SEMANTIC: "meditations_semantic",
        ChunkingStrategy.HIERARCHICAL: "meditations_hierarchical",
    }
    return mapping.get(strategy, "meditations_parent_child")


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    strategy: ChunkingStrategy = Query(ChunkingStrategy.PARENT_CHILD),
    n_results: Optional[int] = Query(None),
    return_parents: Optional[bool] = Query(None),
):
    """
    Query documents using specified chunking strategy.
    
    Parameters:
        request: Query request with query text
        strategy: Chunking strategy (fixed_size, parent_child, semantic, hierarchical)
        n_results: Override number of results (uses request.n_results if not provided)
        return_parents: Override parent context flag
    
    Returns:
        QueryResponse with results from the chosen strategy
    """
    
    # Validate query
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Use overrides if provided, otherwise use request values
    results_count = n_results if n_results is not None else request.n_results
    return_parent_context = return_parents if return_parents is not None else request.return_parents
    
    try:
        # Get the appropriate collection
        collection_name = get_collection_name(strategy)
        print(f"📊 Querying collection: {collection_name}")
        print(f"   Strategy: {strategy.value}")
        print(f"   Query: {request.query}")
        
        try:
            collection = client.get_collection(name=collection_name)
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Collection '{collection_name}' not found. "
                       f"Run ingest_meditations_semantic.py first."
            )
        
        # Query the collection
        results = collection.query(
            query_texts=[request.query],
            n_results=results_count,
            include=["documents", "distances", "metadatas"]
        )
        
        # Transform results to response format
        # ChromaDB returns distances (0-1 range), convert to similarity (1 - distance)
        chunk_results = []
        
        if results["documents"] and len(results["documents"]) > 0:
            for i, doc in enumerate(results["documents"][0]):
                # Convert distance to similarity (ChromaDB uses cosine distance)
                distance = results["distances"][0][i]
                similarity = 1 - distance  # Convert to 0-1 similarity score
                
                chunk_results.append(ChunkResult(
                    id=results["ids"][0][i],
                    text=doc,
                    similarity=similarity,
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {}
                ))
        
        # Calculate metrics
        metrics = {
            "collection": collection_name,
            "strategy": strategy.value,
            "total_documents_in_collection": collection.count(),
            "results_returned": len(chunk_results),
            "avg_similarity": sum(r.similarity for r in chunk_results) / len(chunk_results) if chunk_results else 0,
        }
        
        # Add parent context metadata if available
        if return_parent_context:
            metrics["parent_context_available"] = any(
                "parent" in r.metadata for r in chunk_results
            )
        
        response = QueryResponse(
            strategy=strategy.value,
            query=request.query,
            results=chunk_results,
            total_results=len(chunk_results),
            metrics=metrics
        )
        
        print(f"   ✓ Returned {len(chunk_results)} results")
        print(f"   • Avg similarity: {metrics['avg_similarity']:.3f}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error querying documents: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error querying documents: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        collections = client.list_collections()
        collection_names = [c.name for c in collections]
        
        return {
            "status": "healthy",
            "available_strategies": [
                {
                    "name": "fixed_size",
                    "collection": "meditations_fixed_size",
                    "available": "meditations_fixed_size" in collection_names
                },
                {
                    "name": "parent_child",
                    "collection": "meditations_parent_child",
                    "available": "meditations_parent_child" in collection_names
                },
                {
                    "name": "semantic",
                    "collection": "meditations_semantic",
                    "available": "meditations_semantic" in collection_names
                },
                {
                    "name": "hierarchical",
                    "collection": "meditations_hierarchical",
                    "available": "meditations_hierarchical" in collection_names
                }
            ]
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/strategies")
async def list_strategies():
    """List available chunking strategies and their collections."""
    try:
        collections = client.list_collections()
        collection_names = [c.name for c in collections]
        
        strategies = {}
        for strategy in ChunkingStrategy:
            collection_name = get_collection_name(strategy)
            if collection_name in collection_names:
                col = client.get_collection(name=collection_name)
                strategies[strategy.value] = {
                    "available": True,
                    "collection_name": collection_name,
                    "document_count": col.count(),
                }
            else:
                strategies[strategy.value] = {
                    "available": False,
                    "message": f"Run ingest script for {strategy.value} strategy"
                }
        
        return {"strategies": strategies}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))