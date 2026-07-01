from chunkLab.app.chunkers.semantic_chunker import SemanticChunker
from .fixed_chunker import FixedChunker
from .parent_child_chunker import ParentChildChunker, ParentChildRetriever

# Registry of available chunking strategies
CHUNKERS = {
    "fixed": FixedChunker,
    "parent_child": ParentChildChunker, 
    "semantic": SemanticChunker
}

def get_chunker(strategy: str):
    """Get a chunker by strategy name"""
    if strategy not in CHUNKERS:
        raise ValueError(f"Unknown strategy '{strategy}'. Available: {list(CHUNKERS.keys())}")
    return CHUNKERS[strategy]()

__all__ = ['FixedChunker', 'ParentChildChunker', 'ParentChildRetriever', 'get_chunker', 'CHUNKERS', 'SemanticChunker', 'ChunkingMetrics']