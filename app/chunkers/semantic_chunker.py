"""
SemanticChunker: Split documents by topic boundaries using sentence embeddings.
Instead of fixed-size or hierarchical splits, this detects natural topic changes
via cosine similarity between consecutive sentences.

Usage:
    chunker = SemanticChunker(similarity_threshold=0.5)
    chunks = chunker.chunk(text)
"""

from typing import List, Tuple
import nltk 
from sentence_transformers import SentenceTransformer
import numpy as np
from dataclasses import dataclass


@dataclass
class ChunkingMetrics:
    """Metrics for the chunking process."""
    total_chunks: int
    avg_chunk_size: float
    min_chunk_size: int
    max_chunk_size: int
    avg_similarity_score: float
    total_words: int


class SemanticChunker:
    """
    Chunk documents by semantic boundaries, not size.
    Detects topic changes by measuring cosine similarity between sentence embeddings.
    """

    def __init__(self, similarity_threshold: float = 0.5, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Args:
            similarity_threshold: If similarity between consecutive sentences drops below this,
                                 treat as chunk boundary (0.0-1.0, higher = stricter).
                                 Range: 0.0-1.0
                                 - 0.3: Very sensitive (many small chunks, ~100+)
                                 - 0.5: Moderate (balanced, ~40-60 chunks)
                                 - 0.7: Strict (fewer large chunks, ~20-30)
            model_name: Sentence transformer model. 'all-MiniLM-L6-v2' is lightweight & fast.
        """
        self.threshold = similarity_threshold
        self.model = SentenceTransformer(model_name)
        
        # Download punkt tokenizer if not already present
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)

    def chunk(self, text: str) -> List[str]:
        """
        Split text into semantic chunks by detecting topic boundaries.

        Returns: 
            List of chunks (variable size, semantically coherent)
        """
        # Step 1: Split into sentences
        sentences = nltk.sent_tokenize(text)
        if len(sentences) < 2:
            return [text]

        # Step 2: Embed all sentences at once (more efficient)
        embeddings = self.model.encode(sentences, convert_to_numpy=True)

        # Step 3: Calculate similarities between consecutive sentences
        chunks = []
        current_chunk = [sentences[0]]
        similarities = []  # Track for metrics

        for i in range(1, len(sentences)):
            # Cosine similarity between sentence i-1 and i
            similarity = self._cosine_similarity(embeddings[i - 1], embeddings[i])
            similarities.append(similarity)

            # Step 4: If similarity drops below threshold, start new chunk (topic boundary)
            if similarity < self.threshold:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentences[i]]
            else:
                current_chunk.append(sentences[i])

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def chunk_with_metrics(self, text: str) -> Tuple[List[str], ChunkingMetrics]:
        """
        Chunk text and return metrics about the chunking process.

        Returns:
            Tuple of (chunks, metrics)
        """
        sentences = nltk.sent_tokenize(text)
        if len(sentences) < 2:
            return [text], self._empty_metrics(text)

        embeddings = self.model.encode(sentences, convert_to_numpy=True)

        chunks = []
        current_chunk = [sentences[0]]
        similarities = []

        for i in range(1, len(sentences)):
            similarity = self._cosine_similarity(embeddings[i - 1], embeddings[i])
            similarities.append(similarity)

            if similarity < self.threshold:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentences[i]]
            else:
                current_chunk.append(sentences[i])

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        # Calculate metrics
        chunk_sizes = [len(chunk.split()) for chunk in chunks]
        metrics = ChunkingMetrics(
            total_chunks=len(chunks),
            avg_chunk_size=np.mean(chunk_sizes) if chunk_sizes else 0,
            min_chunk_size=min(chunk_sizes) if chunk_sizes else 0,
            max_chunk_size=max(chunk_sizes) if chunk_sizes else 0,
            avg_similarity_score=np.mean(similarities) if similarities else 0,
            total_words=len(text.split()),
        )

        return chunks, metrics

    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    @staticmethod
    def _empty_metrics(text: str) -> ChunkingMetrics:
        """Return zero metrics for empty/single-sentence text."""
        return ChunkingMetrics(
            total_chunks=1,
            avg_chunk_size=len(text.split()),
            min_chunk_size=len(text.split()),
            max_chunk_size=len(text.split()),
            avg_similarity_score=0,
            total_words=len(text.split()),
        )

    def visualize_chunks(self, text: str, show_similarity: bool = False) -> str:
        """
        Pretty-print chunks for debugging/inspection.

        Args:
            text: Document text
            show_similarity: Whether to show inter-sentence similarities

        Returns:
            Formatted string representation
        """
        sentences = nltk.sent_tokenize(text)
        embeddings = self.model.encode(sentences, convert_to_numpy=True)

        output = []
        current_chunk = [sentences[0]]
        chunk_num = 1

        for i in range(1, len(sentences)):
            similarity = self._cosine_similarity(embeddings[i - 1], embeddings[i])

            if similarity < self.threshold:
                chunk_text = ' '.join(current_chunk)
                output.append(f"\n--- Chunk {chunk_num} ---")
                output.append(chunk_text)
                output.append(f"(Words: {len(chunk_text.split())}, Similarity: {similarity:.3f})")
                current_chunk = [sentences[i]]
                chunk_num += 1
            else:
                current_chunk.append(sentences[i])

        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            output.append(f"\n--- Chunk {chunk_num} ---")
            output.append(chunk_text)
            output.append(f"(Words: {len(chunk_text.split())})")

        return '\n'.join(output)