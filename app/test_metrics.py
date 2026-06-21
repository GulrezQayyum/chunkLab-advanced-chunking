# Copy this test file to your app directory
"""Week 2 Metrics Collection"""
import chromadb
import time
from statistics import mean

def get_metrics():
    client = chromadb.Client()
    collection = client.get_or_create_collection(name="meditations_parent_child")
    
    total_chunks = collection.count()
    
    try:
        all_ids = collection.get()['ids']
        parents = len([id for id in all_ids if '_parent_' in id and '_child_' not in id])
        children = len([id for id in all_ids if '_child_' in id])
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
            scores.append(mean([1 - d for d in results['distances'][0]]))
            print(f"  '{q}': {elapsed:.1f}ms, score: {scores[-1]:.3f}")
    
    print(f"\n✅ RESULTS")
    print(f"  Avg query time: {mean(times):.1f}ms")
    print(f"  Avg similarity: {mean(scores):.3f}")
    print("=" * 60)

if __name__ == "__main__":
    get_metrics()
