class FixedChunker:
    """
    Week 1: The simplest chunking strategy.
    Split text into fixed-size pieces with a small overlap so context
    doesn't get cut off at boundaries.

    Learning goal: understand WHY this is the baseline and where it fails.
    Try it on a document where a concept spans two chunks — notice the
    answer gets worse because the context is split.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[dict]:
        chunks = []
        start = 0
        index = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "id": f"chunk_{index}",
                    "text": chunk_text,
                    "metadata": {
                        "strategy": "fixed",
                        "chunk_index": index,
                        "start_char": start,
                        "end_char": end,
                        "chunk_size": len(chunk_text),
                    }
                })
                index += 1

            # Move forward by chunk_size minus overlap
            # so each chunk shares `overlap` characters with the next
            start += self.chunk_size - self.overlap

        return chunks