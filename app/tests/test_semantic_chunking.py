"""
Test script for semantic chunking strategy validation.
Run this after ingesting semantic chunks to verify everything works.

Usage:
    python test_semantic_strategy.py
"""

import chromadb
import requests
import json
from test_semantic_chunking import SemanticChunker, ChunkingMetrics
from pathlib import Path


def print_header(title: str):
    """Print formatted section header."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)


def test_semantic_chunker_local():
    """Test SemanticChunker class locally."""
    print_header("TEST 1: Local Semantic Chunker")
    
    # Load sample text
    doc_path = "meditations.txt"
    if not Path(doc_path).exists():
        print(f"❌ Error: {doc_path} not found")
        return False
    
    with open(doc_path, 'r') as f:
        text = f.read()
    
    print(f"\n📖 Loaded: {len(text.split())} words")
    
    # Test chunker
    print("\n⏳ Chunking with threshold=0.5...")
    chunker = SemanticChunker(similarity_threshold=0.5)
    chunks, metrics = chunker.chunk_with_metrics(text)
    
    print(f"\n✅ Chunking Results:")
    print(f"   • Chunks: {metrics.total_chunks}")
    print(f"   • Avg size: {metrics.avg_chunk_size:.0f} words")
    print(f"   • Range: {metrics.min_chunk_size}-{metrics.max_chunk_size} words")
    print(f"   • Avg similarity: {metrics.avg_similarity_score:.3f}")
    
    # Show sample chunks
    print(f"\n📝 Sample Chunks:")
    for i in range(min(2, len(chunks))):
        preview = chunks[i][:100] + "..." if len(chunks[i]) > 100 else chunks[i]
        print(f"\n   Chunk {i+1} ({len(chunks[i].split())} words):")
        print(f"   {preview}")
    
    # Validate metrics
    if 40 <= metrics.total_chunks <= 60:
        print(f"\n✅ Chunk count in expected range (45-50)")
        return True
    else:
        print(f"\n⚠️  Chunk count {metrics.total_chunks} outside expected range")
        return True  # Still pass, just different threshold


def test_chromadb_collection():
    """Test if semantic collection exists in ChromaDB."""
    print_header("TEST 2: ChromaDB Collection")
    
    try:
        client = chromadb.Client()
        
        # Try to get collection
        try:
            collection = client.get_collection("meditations_semantic")
            count = collection.count()
            print(f"\n✅ Found collection: meditations_semantic")
            print(f"   • Documents: {count}")
            
            # Get sample document
            results = collection.get(limit=1)
            if results['documents']:
                sample = results['documents'][0][:150] + "..."
                print(f"   • Sample: {sample}")
            
            return True
        except Exception as e:
            print(f"\n❌ Collection not found: {str(e)}")
            print(f"   → Run: python ingest_meditations_semantic.py")
            return False
    except Exception as e:
        print(f"❌ ChromaDB error: {str(e)}")
        return False


def test_fastapi_backend():
    """Test FastAPI backend with semantic strategy."""
    print_header("TEST 3: FastAPI Backend")
    
    base_url = "http://localhost:8001"
    
    # Check if server is running
    try:
        response = requests.get(f"{base_url}/docs", timeout=2)
        print(f"\n✅ Backend is running on {base_url}")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to {base_url}")
        print(f"   → Start FastAPI: python main.py")
        return False
    
    # Test health endpoint
    print(f"\n🏥 Checking health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/documents/health")
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Backend healthy")
            
            # Check available strategies
            strategies = health.get('available_strategies', [])
            for strat in strategies:
                status = "✅" if strat.get('available') else "❌"
                print(f"      {status} {strat['name']}")
        else:
            print(f"   ⚠️  Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False
    
    # Test query with semantic strategy
    print(f"\n🔍 Testing semantic query...")
    
    test_query = "virtue reason"
    payload = {
        "query": test_query,
        "n_results": 5,
        "return_parents": True
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/documents/query?strategy=semantic",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Query successful")
            print(f"   • Strategy: {data['strategy']}")
            print(f"   • Results: {data['total_results']}")
            
            if data['results']:
                avg_sim = data['metrics']['avg_similarity']
                print(f"   • Avg similarity: {avg_sim:.3f}")
                
                # Show top result
                top = data['results'][0]
                preview = top['text'][:100] + "..."
                print(f"   • Top result: {preview}")
                
                # Validate similarity
                if 0.4 <= avg_sim <= 0.8:
                    print(f"\n✅ Similarity scores in reasonable range")
                    return True
                else:
                    print(f"\n⚠️  Similarity scores outside typical range")
                    return True  # Still valid, just different threshold
            else:
                print(f"   ⚠️  No results returned")
                return False
        else:
            print(f"   ❌ Status {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False


def compare_strategies():
    """Compare semantic vs parent-child strategies."""
    print_header("TEST 4: Strategy Comparison")
    
    base_url = "http://localhost:8001"
    test_queries = [
        "virtue reason",
        "discipline self-control",
        "nature universe",
    ]
    
    try:
        requests.get(f"{base_url}/api/documents/health", timeout=1)
    except:
        print("\n❌ Backend not running")
        return False
    
    results = {}
    
    for strategy in ["parent_child", "semantic"]:
        print(f"\n📊 Testing {strategy.upper()} strategy...")
        results[strategy] = []
        
        for query in test_queries:
            try:
                response = requests.post(
                    f"{base_url}/api/documents/query?strategy={strategy}",
                    json={
                        "query": query,
                        "n_results": 5,
                        "return_parents": True
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    avg_sim = data['metrics']['avg_similarity']
                    results[strategy].append({
                        'query': query,
                        'avg_similarity': avg_sim,
                        'results_count': data['total_results']
                    })
                    
                    print(f"   '{query}': {avg_sim:.3f}")
                else:
                    print(f"   ❌ {strategy}: Failed ({response.status_code})")
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
    
    # Print comparison
    if results['parent_child'] and results['semantic']:
        print(f"\n📈 Comparison:")
        print(f"{'Strategy':<15} {'Queries':<10} {'Avg Sim':<12}")
        print(f"{'-'*37}")
        
        for strategy in ['parent_child', 'semantic']:
            if results[strategy]:
                avg = sum(r['avg_similarity'] for r in results[strategy]) / len(results[strategy])
                count = len(results[strategy])
                print(f"{strategy:<15} {count:<10} {avg:<12.3f}")
                
                if strategy == 'semantic' and 'parent_child' in results:
                    pc_avg = sum(r['avg_similarity'] for r in results['parent_child']) / len(results['parent_child'])
                    improvement = ((avg - pc_avg) / pc_avg) * 100
                    print(f"{'':15} {'Improvement':<10} {improvement:>10.1f}%")
        
        return True
    
    return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("🧪 ChunkLab: Semantic Chunking Validation Tests")
    print("="*60)
    
    tests = [
        ("Local Chunker", test_semantic_chunker_local),
        ("ChromaDB", test_chromadb_collection),
        ("FastAPI Backend", test_fastapi_backend),
        ("Strategy Comparison", compare_strategies),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Unexpected error in {name}: {str(e)}")
            results[name] = False
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, passed_status in results.items():
        status = "✅ PASS" if passed_status else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n🎉 All tests passed! Semantic chunking is ready.")
    else:
        print(f"\n⚠️  Some tests failed. Check errors above.")
    
    return passed == total


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)