"""
ParentChildChunker for ChunkLab Week 2
Implements hierarchical chunking with child-to-parent mapping
Child chunks: 256-512 tokens (retrieval granularity)
Parent chunks: 1024-2048 tokens (context for LLM)
"""

import re
from typing import List, Dict, Tuple
from dataclasses import dataclass
import uuid


@dataclass
class Chunk:
    """Represents a chunk with metadata"""
    id: str
    text: str
    token_count: int
    metadata: Dict


class ParentChildChunker:
    """
    Hierarchical chunking strategy:
    1. Split document into parent chunks (larger, overlapping)
    2. Split each parent into child chunks (smaller, for retrieval)
    3. Maintain parent_id reference in child metadata
    4. Retrieve child → return parent for context
    """

    def __init__(
        self,
        parent_chunk_size: int = 1500,      # tokens
        parent_overlap: int = 200,           # tokens
        child_chunk_size: int = 400,         # tokens
        child_overlap: int = 50,             # tokens
    ):
        self.parent_chunk_size = parent_chunk_size
        self.parent_overlap = parent_overlap
        self.child_chunk_size = child_chunk_size
        self.child_overlap = child_overlap

    def _estimate_tokens(self, text: str) -> int:
        """Simple token estimation (word-count based)"""
        return len(text.split())

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences while preserving structure"""
        # Basic sentence splitting (can be improved with NLTK/spaCy)
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def _create_chunks_with_overlap(
        self,
        sentences: List[str],
        chunk_token_size: int,
        overlap_token_size: int,
    ) -> List[Tuple[str, int]]:
        """
        Create chunks from sentences with overlap
        Returns: List of (chunk_text, token_count) tuples
        """
        chunks = []
        current_chunk = []
        current_tokens = 0
        overlap_buffer = []
        overlap_tokens = 0

        for sentence in sentences:
            sentence_tokens = self._estimate_tokens(sentence)

            # Check if adding this sentence exceeds chunk size
            if current_tokens + sentence_tokens > chunk_token_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append((chunk_text, current_tokens))

                # Prepare overlap for next chunk
                overlap_buffer = current_chunk.copy()
                overlap_tokens = current_tokens

                # Create overlap segment
                current_chunk = []
                current_tokens = 0

                # Add overlap sentences to new chunk
                while overlap_buffer and overlap_tokens > overlap_token_size:
                    removed = overlap_buffer.pop(0)
                    overlap_tokens -= self._estimate_tokens(removed)

                current_chunk = overlap_buffer.copy()
                current_tokens = overlap_tokens

            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append((chunk_text, current_tokens))

        return chunks

    def chunk(self, text: str, doc_id: str) -> Dict[str, List[Chunk]]:
        """
        Create parent and child chunks from document
        
        Returns:
            {
                'parents': [Chunk, ...],
                'children': [Chunk, ...],
                'parent_child_map': {parent_id: [child_id, ...]}
            }
        """
        sentences = self._split_into_sentences(text)

        # Step 1: Create parent chunks (larger, with overlap)
        parent_chunk_tuples = self._create_chunks_with_overlap(
            sentences,
            self.parent_chunk_size,
            self.parent_overlap,
        )

        parents = []
        children = []
        parent_child_map = {}

        # Step 2: For each parent, create child chunks
        for parent_idx, (parent_text, parent_tokens) in enumerate(parent_chunk_tuples):
            parent_id = f"{doc_id}_parent_{parent_idx}"

            # Create parent chunk
            parent = Chunk(
                id=parent_id,
                text=parent_text,
                token_count=parent_tokens,
                metadata={
                    'doc_id': doc_id,
                    'chunk_type': 'parent',
                    'parent_index': parent_idx,
                    'strategy': 'parent_child',
                },
            )
            parents.append(parent)
            parent_child_map[parent_id] = []

            # Split parent into child chunks
            parent_sentences = re.split(r'(?<=[.!?])\s+', parent_text.strip())
            child_chunk_tuples = self._create_chunks_with_overlap(
                parent_sentences,
                self.child_chunk_size,
                self.child_overlap,
            )

            for child_idx, (child_text, child_tokens) in enumerate(child_chunk_tuples):
                child_id = f"{parent_id}_child_{child_idx}"

                # Create child chunk with parent reference
                child = Chunk(
                    id=child_id,
                    text=child_text,
                    token_count=child_tokens,
                    metadata={
                        'doc_id': doc_id,
                        'chunk_type': 'child',
                        'parent_id': parent_id,
                        'parent_index': parent_idx,
                        'child_index': child_idx,
                        'strategy': 'parent_child',
                    },
                )
                children.append(child)
                parent_child_map[parent_id].append(child_id)

        return {
            'parents': parents,
            'children': children,
            'parent_child_map': parent_child_map,
        }


class ParentChildRetriever:
    """
    Retrieval strategy: retrieve child chunks, return parent context
    """

    def __init__(self, chroma_client, collection_name: str):
        self.collection = chroma_client.get_collection(collection_name)
        self.chroma_client = chroma_client

    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        return_parents: bool = True,
    ) -> List[Dict]:
        """
        Retrieve child chunks matching query, optionally return parent context
        
        Args:
            query: Search query
            n_results: Number of child chunks to retrieve
            return_parents: If True, return full parent chunks instead of children
            
        Returns:
            List of chunks (children or parents) with metadata
        """
        # Query collection for child chunks
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            include=['embeddings', 'documents', 'metadatas', 'distances']
        )

        if not results['documents'] or not results['documents'][0]:
            return []

        retrieved_chunks = []
        parent_ids_to_fetch = set()

        # Process child chunks
        for i, (chunk_text, metadata, distance) in enumerate(
            zip(results['documents'][0], results['metadatas'][0], results['distances'][0])
        ):
            retrieved_chunks.append({
                'chunk_id': results['ids'][0][i] if results['ids'] else f'chunk_{i}',
                'text': chunk_text,
                'metadata': metadata,
                'similarity_score': 1 - distance,  # Convert distance to similarity
                'chunk_type': 'child',
            })

            # Collect parent IDs if we need to fetch parents
            if return_parents and metadata.get('parent_id'):
                parent_ids_to_fetch.add(metadata['parent_id'])

        # Fetch parent chunks if requested
        if return_parents and parent_ids_to_fetch:
            parent_chunks = self.collection.get(
                ids=list(parent_ids_to_fetch),
                include=['documents', 'metadatas']
            )

            # Map parents back to children
            parent_map = {}
            for parent_id, parent_text, parent_metadata in zip(
                parent_chunks['ids'],
                parent_chunks['documents'],
                parent_chunks['metadatas']
            ):
                parent_map[parent_id] = {
                    'text': parent_text,
                    'metadata': parent_metadata,
                }

            # Augment child chunks with parent context
            for chunk in retrieved_chunks:
                parent_id = chunk['metadata'].get('parent_id')
                if parent_id in parent_map:
                    chunk['parent_context'] = parent_map[parent_id]
                    chunk['chunk_type'] = 'child_with_parent'

        return retrieved_chunks