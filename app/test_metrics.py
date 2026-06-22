"""Week 2 Metrics Collection"""
import chromadb
import time
from statistics import mean

def get_metrics():
    # Use the same persistent client as ingestion
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(name="meditations_parent_child")
    
    total_chunks = collection.count()
    
    try:
        all_ids = collection.get()['ids']
        # Count parents: IDs that contain "parent" but not "child" (safe)
        parents = len([id for id in all_ids if "parent" in id and "child" not in id])
        # Count children: IDs that contain "child"
        children = len([id for id in all_ids if "child" in id])
    except:
        parents = children = 0
    
    print("=" * 60)
    print("WEEK 2: PARENT-CHILD CHUNKING METRICS")
    print("=" * 60)
    print(f"\n📊 DATABASE")
    print(f"  Total: {total_chunks}")
    print(f"  Parents: {parents}")
    print(f"  Children: {children}")
    
    queries = ["virtue reason", "stoicism discipline", "mind consciousness"]
    times, scores = [], []
    
    print(f"\n⚡ QUERIES")
    for q in queries:
        start = time.time()
        results = collection.query(query_texts=[q], n_results=3, include=['distances'])
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        
        if results['distances'][0]:
            # Cosine distance: similarity = 1 - distance
            sims = [1 - d for d in results['distances'][0]]
            avg_sim = mean(sims)
            scores.append(avg_sim)
            print(f"  '{q}': {elapsed:.1f}ms, score: {avg_sim:.3f}")
        else:
            print(f"  '{q}': {elapsed:.1f}ms, no results found")
    
    print(f"\n✅ RESULTS")
    print(f"  Avg query time: {mean(times):.1f}ms")
    if scores:
        print(f"  Avg similarity: {mean(scores):.3f}")
    else:
        print("  Avg similarity: N/A (no results returned)")
    print("=" * 60)

if __name__ == "__main__":
    get_metrics()