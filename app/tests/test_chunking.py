"""
ChunkLab Week 2: Benchmarking & Testing
Compare parent-child chunking (Week 2) vs fixed-size chunking (Week 1)
"""

import json
from typing import List, Dict, Tuple
from dataclasses import asdict
from chunkers import ParentChildChunker, ParentChildRetriever

class ChunkLabBenchmark:
    """
    Benchmark suite for evaluating chunking strategies
    Focus: semantic retrieval quality
    """

    # Test queries specifically targeting semantic relationships
    SEMANTIC_TEST_QUERIES = [
        {
            'query': 'What is virtue?',
            'expected_themes': ['virtue', 'excellence', 'character', 'moral'],
            'description': 'Core philosophical concept — fixed-size may fragment'
        },
        {
            'query': 'How should I handle adversity?',
            'expected_themes': ['adversity', 'resilience', 'suffering', 'acceptance'],
            'description': 'Requires context spanning multiple sentences'
        },
        {
            'query': 'What is the role of duty in life?',
            'expected_themes': ['duty', 'responsibility', 'purpose', 'discipline'],
            'description': 'Abstract concept needing complete arguments'
        },
        {
            'query': 'How do I achieve tranquility?',
            'expected_themes': ['tranquility', 'peace', 'mind', 'control'],
            'description': 'Process/journey — needs semantic coherence'
        },
        {
            'query': 'What is the nature of death?',
            'expected_themes': ['death', 'mortality', 'fear', 'acceptance'],
            'description': 'Existential topic — requires full argument context'
        },
    ]

    def __init__(self, document_text: str):
        self.document_text = document_text
        self.chunker_pc = ParentChildChunker(
            parent_chunk_size=1500,
            parent_overlap=200,
            child_chunk_size=400,
            child_overlap=50,
        )

    def _calculate_chunk_coverage(self, chunks: List[str], query_terms: List[str]) -> Dict:
        """
        Analyze how well chunks cover semantic topics
        Returns: coverage metrics
        """
        coverage = {
            'total_chunks': len(chunks),
            'chunks_with_terms': 0,
            'term_distribution': {},
            'context_continuity': 0,
        }

        for term in query_terms:
            coverage['term_distribution'][term] = 0

        # Check term presence
        for chunk in chunks:
            chunk_lower = chunk.lower()
            terms_found = []

            for term in query_terms:
                if term.lower() in chunk_lower:
                    coverage['term_distribution'][term] += 1
                    terms_found.append(term)

            if terms_found:
                coverage['chunks_with_terms'] += 1

        # Calculate context continuity (how chunks relate to each other)
        if len(chunks) > 1:
            # Simple metric: adjacent chunks share terms
            shared_terms = 0
            for i in range(len(chunks) - 1):
                chunk1_terms = set(chunks[i].lower().split())
                chunk2_terms = set(chunks[i + 1].lower().split())
                overlap = len(chunk1_terms & chunk2_terms)
                shared_terms += overlap

            coverage['context_continuity'] = shared_terms / (len(chunks) - 1) if len(chunks) > 1 else 0

        return coverage

    def benchmark_semantic_retrieval(self) -> Dict:
        """
        Benchmark parent-child chunking on semantic test queries
        
        Returns:
            {
                'strategy': 'parent_child',
                'total_tests': 5,
                'tests': [
                    {
                        'query': '...',
                        'results': {
                            'parent_chunks_analyzed': 3,
                            'child_chunks_analyzed': 12,
                            'semantic_coverage': {...},
                            'avg_chunk_tokens': 420,
                            'context_quality': 'high'
                        }
                    }
                ]
            }
        """
        results = ParentChildChunker.chunk(self.document_text, 'benchmark_doc')

        benchmark_results = {
            'strategy': 'parent_child',
            'total_tests': len(self.SEMANTIC_TEST_QUERIES),
            'tests': [],
            'summary': {
                'total_parents': len(results['parents']),
                'total_children': len(results['children']),
                'avg_parent_tokens': sum(c.token_count for c in results['parents']) / len(results['parents']),
                'avg_child_tokens': sum(c.token_count for c in results['children']) / len(results['children']),
            }
        }

        for test_case in self.SEMANTIC_TEST_QUERIES:
            query = test_case['query']
            expected_themes = test_case['expected_themes']

            # Simulate retrieval: find chunks containing expected themes
            child_chunks_matched = []
            parent_chunks_matched = set()

            for child in results['children']:
                for theme in expected_themes:
                    if theme.lower() in child.text.lower():
                        child_chunks_matched.append(child.text)
                        parent_id = child.metadata.get('parent_id')
                        if parent_id:
                            parent_chunks_matched.add(parent_id)
                        break

            # Get parent chunks
            parent_chunks_text = []
            for parent in results['parents']:
                if parent.id in parent_chunks_matched:
                    parent_chunks_text.append(parent.text)

            # Calculate coverage
            coverage = self._calculate_chunk_coverage(parent_chunks_text, expected_themes)

            # Quality assessment
            context_quality = 'high' if len(parent_chunks_matched) >= 2 else (
                'medium' if len(parent_chunks_matched) == 1 else 'low'
            )

            test_result = {
                'query': query,
                'description': test_case['description'],
                'expected_themes': expected_themes,
                'results': {
                    'child_chunks_matched': len(child_chunks_matched),
                    'parent_chunks_matched': len(parent_chunks_matched),
                    'semantic_coverage': coverage,
                    'avg_matched_chunk_tokens': (
                        sum(c.token_count for c in results['children'] if c.text in child_chunks_matched) / 
                        len(child_chunks_matched) if child_chunks_matched else 0
                    ),
                    'context_quality': context_quality,
                },
            }

            benchmark_results['tests'].append(test_result)

        return benchmark_results

    def compare_strategies(self) -> Dict:
        """
        Comparison: Parent-Child (Week 2) vs Fixed-Size (Week 1)
        
        Simulates Week 1 chunking for comparison
        """
        from typing import List

        # Simulate fixed-size chunking (Week 1)
        def simple_fixed_size_split(text: str, chunk_size: int = 500) -> List[str]:
            words = text.split()
            chunks = []
            current_chunk = []
            current_size = 0

            for word in words:
                current_chunk.append(word)
                current_size += 1
                if current_size >= chunk_size:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_size = 0

            if current_chunk:
                chunks.append(' '.join(current_chunk))

            return chunks

        # Fixed-size chunks (Week 1)
        week1_chunks = simple_fixed_size_split(self.document_text, chunk_size=500)

        # Parent-child chunks (Week 2)
        week2_result = self._parent_child_chunker.chunk(self.document_text, 'compare_doc')

        comparison = {
            'week1_fixed_size': {
                'strategy': 'fixed_size',
                'total_chunks': len(week1_chunks),
                'avg_chunk_tokens': sum(len(c.split()) for c in week1_chunks) / len(week1_chunks),
                'fragmentation_risk': 'high',  # Semantic boundaries not respected
            },
            'week2_parent_child': {
                'strategy': 'parent_child',
                'total_parents': len(week2_result['parents']),
                'total_children': len(week2_result['children']),
                'avg_parent_tokens': sum(c.token_count for c in week2_result['parents']) / len(week2_result['parents']),
                'avg_child_tokens': sum(c.token_count for c in week2_result['children']) / len(week2_result['children']),
                'fragmentation_risk': 'low',  # Children are granular but parents maintain context
            },
            'analysis': {
                'week1_chunks': len(week1_chunks),
                'week2_children': len(week2_result['children']),
                'week2_parents': len(week2_result['parents']),
                'expected_improvement': 'Week 2 retrieves small, semantic units but provides large, contextual parents to LLM',
                'use_case_advantage': 'Semantic queries (virtue, duty, resilience) will retrieve complete arguments vs fragmented answers',
            }
        }

        return comparison


# ============================================================================
# Test Runner
# ============================================================================

def run_week2_tests(document_path: str = None, sample_text: str = None):
    """
    Run full test suite for Week 2
    
    Provide either:
    - document_path: path to .txt file with Meditations document
    - sample_text: inline document text
    """

    if document_path:
        with open(document_path, 'r', encoding='utf-8') as f:
            doc_text = f.read()
    elif sample_text:
        doc_text = sample_text
    else:
        raise ValueError("Provide either document_path or sample_text")

    print("\n" + "="*80)
    print("CHUNKLAB WEEK 2: PARENT-CHILD CHUNKING TESTS")
    print("="*80)

    benchmark = ChunkLabBenchmark(doc_text)

    # Run semantic retrieval benchmark
    print("\n[1/2] Running Semantic Retrieval Benchmark...")
    semantic_results = benchmark.benchmark_semantic_retrieval()

    print(f"\nTotal Test Queries: {semantic_results['total_tests']}")
    print(f"Document Stats:")
    print(f"  - Parent Chunks: {semantic_results['summary']['total_parents']}")
    print(f"  - Child Chunks: {semantic_results['summary']['total_children']}")
    print(f"  - Avg Parent Tokens: {semantic_results['summary']['avg_parent_tokens']:.0f}")
    print(f"  - Avg Child Tokens: {semantic_results['summary']['avg_child_tokens']:.0f}")

    print("\nSemantic Test Results:")
    for test in semantic_results['tests']:
        print(f"\n  Query: {test['query']}")
        print(f"  Description: {test['description']}")
        print(f"  Expected Themes: {', '.join(test['expected_themes'])}")
        print(f"  - Children Matched: {test['results']['child_chunks_matched']}")
        print(f"  - Parent Chunks Retrieved: {test['results']['parent_chunks_matched']}")
        print(f"  - Context Quality: {test['results']['context_quality']}")
        print(f"  - Avg Chunk Size: {test['results']['avg_matched_chunk_tokens']:.0f} tokens")

    # Run strategy comparison
    print("\n[2/2] Comparing Week 1 vs Week 2...")
    comparison = benchmark.compare_strategies()

    print("\nWeek 1 (Fixed-Size Chunking):")
    w1 = comparison['week1_fixed_size']
    print(f"  - Total Chunks: {w1['total_chunks']}")
    print(f"  - Avg Chunk Size: {w1['avg_chunk_tokens']:.0f} tokens")
    print(f"  - Fragmentation Risk: {w1['fragmentation_risk']}")

    print("\nWeek 2 (Parent-Child Chunking):")
    w2 = comparison['week2_parent_child']
    print(f"  - Parent Chunks: {w2['total_parents']}")
    print(f"  - Child Chunks: {w2['total_children']}")
    print(f"  - Avg Parent Tokens: {w2['avg_parent_tokens']:.0f}")
    print(f"  - Avg Child Tokens: {w2['avg_child_tokens']:.0f}")
    print(f"  - Fragmentation Risk: {w2['fragmentation_risk']}")

    print("\nComparison Analysis:")
    print(f"  {comparison['analysis']['expected_improvement']}")
    print(f"  Use Case: {comparison['analysis']['use_case_advantage']}")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

    return {
        'semantic_results': semantic_results,
        'comparison': comparison,
    }


if __name__ == "__main__":
    # Example usage
    print("To run tests, call: run_week2_tests(document_path='path/to/meditations.txt')")
    print("Or provide sample_text directly")