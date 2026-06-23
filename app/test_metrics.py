"""Week 2 Metrics Collection"""
import chromadb
import time
from statistics import mean

def get_metrics():
    client = chromadb.PersistentClient(path="./chroma_db")
    # No embedding_function provided – uses the one stored in the collection
    collection = client.get_collection(name="meditations_parent_child")
    
    total = collection.count()
    all_ids = collection.get()['ids']
    parents = len([id for id in all_ids if "parent" in id and "child" not in id])
    children = len([id for id in all_ids if "child" in id])
    
    print("=" * 60)
    print("WEEK 2: PARENT-CHILD CHUNKING METRICS")
    print("=" * 60)
    print(f"\n📊 DATABASE")
    print(f"  Total: {total}")
    print(f"  Parents: {parents}")
    print(f"  Children: {children}")
    
    queries = [
        "What is the role of virtue and reason in Stoic philosophy?",
        "How does Stoicism define discipline and self-control?",
        "What does Marcus Aurelius say about mind and consciousness?"
    ]
    
    times, best_scores = [], []
    print(f"\n⚡ QUERIES")
    for q in queries:
        start = time.time()
        results = collection.query(
            query_texts=[q],
            n_results=3,
            include=['distances', 'documents']
        )
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        
        if results['distances'][0]:
            best_dist = min(results['distances'][0])
            best_sim = 1 - best_dist
            best_scores.append(best_sim)
            print(f"\n  Query: '{q[:60]}...'")
            print(f"    Best distance: {best_dist:.3f}")
            print(f"    Best similarity: {best_sim:.3f}")
            print(f"    Top text (first 150 chars): {results['documents'][0][0][:150]}...")
        else:
            print(f"  No results for: {q[:30]}")
    
    print(f"\n✅ RESULTS")
    print(f"  Avg query time: {mean(times):.1f}ms")
    if best_scores:
        print(f"  Avg best similarity: {mean(best_scores):.3f}")
    else:
        print("  No scores available.")
    print("=" * 60)

if __name__ == "__main__":
    get_metrics()