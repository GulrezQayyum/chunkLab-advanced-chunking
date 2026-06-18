from .fixed_chunker import FixedChunker

# Week 2: from .parent_child_chunker import ParentChildChunker
# Week 3: from .semantic_chunker import SemanticChunker
# Week 4: from .late_chunker import LateChunker

CHUNKERS = {
    "fixed": FixedChunker,
    # "parent_child": ParentChildChunker,   # unlock week 2
    # "semantic": SemanticChunker,           # unlock week 3
    # "late": LateChunker,                   # unlock week 4
}

def get_chunker(strategy: str):
    if strategy not in CHUNKERS:
        raise ValueError(f"Unknown strategy '{strategy}'. Available: {list(CHUNKERS.keys())}")
    return CHUNKERS[strategy]()