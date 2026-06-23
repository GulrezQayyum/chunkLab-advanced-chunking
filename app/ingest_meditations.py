import chromadb
from chromadb.utils import embedding_functions
import re
import os

TEXT_FILE = "meditations.txt"
COLLECTION_NAME = "meditations_parent_child"
CHILD_SIZE = 1200          # characters per child
OVERLAP = 200              # overlap between chunks to preserve continuity
EMBED_MODEL = "all-mpnet-base-v2"   # stronger model

# 1. Read the text
with open(TEXT_FILE, "r", encoding="utf-8") as f:
    raw = f.read()

# 2. Split into books (parent chunks)
book_pattern = r"(BOOK\s+[IVXLCDM]+\.)"
parts = re.split(book_pattern, raw)
books = []
for i in range(1, len(parts), 2):
    title = parts[i].strip()
    content = parts[i+1].strip() if i+1 < len(parts) else ""
    if content:
        books.append((title, content))

if not books:
    books = [("Entire Work", raw)]

print(f"Found {len(books)} parent chunks.")

# 3. Initialize ChromaDB with the embedding function
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBED_MODEL,
    normalize_embeddings=True
)

client = chromadb.PersistentClient(path="./chroma_db")
try:
    client.delete_collection(COLLECTION_NAME)
except:
    pass
collection = client.create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_fn
)

all_ids = []
all_docs = []
all_metadatas = []

# 4. Process each book
for book_idx, (title, content) in enumerate(books):
    # Parent chunk
    parent_id = f"parent_{book_idx:04d}"
    all_ids.append(parent_id)
    all_docs.append(content)
    all_metadatas.append({
        "type": "parent",
        "book_title": title,
        "book_index": book_idx
    })
    
    # Split content into paragraphs (by double newline)
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    # If no paragraphs, split by single newline
    if not paragraphs:
        paragraphs = [p.strip() for p in content.split("\n") if p.strip()]
    # If still empty, treat as one
    if not paragraphs:
        paragraphs = [content]
    
    # Build child chunks with overlap
    child_texts = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) < CHILD_SIZE:
            current += para + " "
        else:
            if current:
                child_texts.append(current.strip())
            # Start new chunk with overlap from the end of previous
            if len(current) > OVERLAP:
                overlap_text = current[-OVERLAP:]
                current = overlap_text + " " + para + " "
            else:
                current = para + " "
    if current:
        child_texts.append(current.strip())
    
    # Add child chunks
    for child_idx, chunk in enumerate(child_texts):
        child_id = f"child_{book_idx:04d}_{child_idx:04d}"
        all_ids.append(child_id)
        all_docs.append(chunk)
        all_metadatas.append({
            "type": "child",
            "parent_id": parent_id,
            "book_title": title,
            "book_index": book_idx
        })

print(f"Total chunks: {len(all_ids)} (parents: {len(books)}, children: {len(all_ids)-len(books)})")

# 5. Add in batches (ChromaDB handles embedding)
BATCH_SIZE = 100
for i in range(0, len(all_ids), BATCH_SIZE):
    batch_ids = all_ids[i:i+BATCH_SIZE]
    batch_docs = all_docs[i:i+BATCH_SIZE]
    batch_meta = all_metadatas[i:i+BATCH_SIZE]
    collection.add(
        ids=batch_ids,
        documents=batch_docs,
        metadatas=batch_meta
    )
    print(f"Added batch {i//BATCH_SIZE + 1}/{(len(all_ids)-1)//BATCH_SIZE + 1}")

print(f"✅ Ingestion complete! Collection now has {collection.count()} chunks.")