import chromadb
from sentence_transformers import SentenceTransformer
import re
import uuid

# ---------- Configuration ----------
TEXT_FILE = "meditations.txt"          # your file name
COLLECTION_NAME = "meditations_parent_child"
CHUNK_SIZE = 2000                      # approximate characters per parent chunk
CHILD_SIZE = 350                       # approximate characters per child chunk
EMBED_MODEL = "all-MiniLM-L6-v2"       # small, fast, good quality
# ------------------------------------

# 1. Load embedding model
print("Loading embedding model...")
model = SentenceTransformer(EMBED_MODEL)

# 2. Read the text
with open(TEXT_FILE, "r", encoding="utf-8") as f:
    raw_text = f.read()

# 3. Split into "books" (parent chunks) using the pattern "BOOK X." or "BOOK X."
#    We'll use a simple regex to split on "BOOK" followed by a Roman numeral.
book_pattern = r"(BOOK\s+[IVXLCDM]+\.)"
book_splits = re.split(book_pattern, raw_text)
books = []
# The first split might be empty or introductory text; skip it.
for i in range(1, len(book_splits), 2):
    title = book_splits[i].strip()
    content = book_splits[i+1].strip() if i+1 < len(book_splits) else ""
    # Keep only if we have content
    if content:
        books.append((title, content))

# If the regex didn't capture books (e.g., if the text is different), fallback:
if not books:
    # Fallback: split by double newline or by "BOOK" without period, etc.
    # Simpler: treat entire text as one parent (not ideal, but works)
    books = [("Entire Work", raw_text)]

print(f"Found {len(books)} parent chunks (books).")

# 4. Create ChromaDB client and collection
client = chromadb.PersistentClient(path="./chroma_db")  # persistent storage
# Delete existing collection if you want a clean start
try:
    client.delete_collection(COLLECTION_NAME)
except:
    pass
collection = client.create_collection(name=COLLECTION_NAME)

# 5. Prepare parent and child chunks
parent_ids = []
child_ids = []
all_texts = []
all_metadatas = []
all_ids = []

for book_idx, (title, content) in enumerate(books):
    # --- Parent chunk ---
    parent_id = f"parent_{book_idx:04d}"
    parent_ids.append(parent_id)
    all_texts.append(content)
    all_metadatas.append({
        "type": "parent",
        "book_title": title,
        "book_index": book_idx
    })
    all_ids.append(parent_id)

    # --- Child chunks: split content into smaller pieces ---
    # Simple split by sentence or paragraph; we'll use a sliding window by character count
    # but for better quality, split by periods and newlines.
    # We'll use regex to split on '. ' or '.\n' or '?\n' etc.
    sentences = re.split(r'(?<=[.!?])\s+', content)
    child_texts = []
    current = ""
    for sent in sentences:
        if len(current) + len(sent) < CHILD_SIZE:
            current += sent + " "
        else:
            if current:
                child_texts.append(current.strip())
            current = sent + " "
    if current:
        child_texts.append(current.strip())

    # If no child texts (very short content), just use the whole as a child
    if not child_texts:
        child_texts = [content]

    for child_idx, child_text in enumerate(child_texts):
        child_id = f"child_{book_idx:04d}_{child_idx:04d}"
        child_ids.append(child_id)
        all_texts.append(child_text)
        all_metadatas.append({
            "type": "child",
            "parent_id": parent_id,
            "book_title": title,
            "book_index": book_idx
        })
        all_ids.append(child_id)

print(f"Total chunks: {len(all_ids)} (parents: {len(parent_ids)}, children: {len(child_ids)})")

# 6. Embed and store in batches (to avoid memory issues)
BATCH_SIZE = 100
for i in range(0, len(all_ids), BATCH_SIZE):
    batch_ids = all_ids[i:i+BATCH_SIZE]
    batch_texts = all_texts[i:i+BATCH_SIZE]
    batch_metadatas = all_metadatas[i:i+BATCH_SIZE]
    print(f"Embedding batch {i//BATCH_SIZE + 1}/{(len(all_ids)-1)//BATCH_SIZE + 1}...")
    embeddings = model.encode(batch_texts).tolist()
    collection.add(
        ids=batch_ids,
        documents=batch_texts,
        embeddings=embeddings,
        metadatas=batch_metadatas
    )

print(f"✅ Ingestion complete! Collection '{COLLECTION_NAME}' now has {collection.count()} chunks.")
print("You can now run: python test_metrics.py")