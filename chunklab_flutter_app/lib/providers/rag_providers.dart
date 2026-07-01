import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:chunklab_flutter_app/services/rag_service.dart';
import 'package:chunklab_flutter_app/models/query_models.dart';

/// Enumeration of supported chunking strategies
enum ChunkingStrategy {
  fixedSize,
  parentChild,
  semantic,
  hierarchical; // For future use

  /// Get the API value for this strategy
  String get value {
    switch (this) {
      case ChunkingStrategy.fixedSize:
        return 'fixed_size';
      case ChunkingStrategy.parentChild:
        return 'parent_child';
      case ChunkingStrategy.semantic:
        return 'semantic';
      case ChunkingStrategy.hierarchical:
        return 'hierarchical';
    }
  }

  /// Get the display label for this strategy
  String get label {
    switch (this) {
      case ChunkingStrategy.fixedSize:
        return 'Fixed-Size';
      case ChunkingStrategy.parentChild:
        return 'Parent-Child';
      case ChunkingStrategy.semantic:
        return 'Semantic';
      case ChunkingStrategy.hierarchical:
        return 'Hierarchical';
    }
  }

  /// Get a brief description of the strategy
  String get description {
    switch (this) {
      case ChunkingStrategy.fixedSize:
        return 'Split by word count (~500 words)';
      case ChunkingStrategy.parentChild:
        return 'Hierarchical with parent context';
      case ChunkingStrategy.semantic:
        return 'Split by topic boundaries';
      case ChunkingStrategy.hierarchical:
        return 'Multi-level summaries';
    }
  }
}

// ============================================================================
// EXISTING PROVIDERS (Keep these as-is)
// ============================================================================


/// RAG service provider
final ragServiceProvider = Provider((ref) => RAGService());

/// Text input provider
final queryTextProvider = StateProvider<String>((ref) => '');

// ============================================================================
// NEW PROVIDER: Strategy Selection
// ============================================================================

/// Selected chunking strategy provider
/// Default to parent_child (most battle-tested)
final selectedStrategyProvider = StateProvider<ChunkingStrategy>(
  (ref) => ChunkingStrategy.parentChild,
);

// ============================================================================
// UPDATED PROVIDER: Query Results with Strategy
// ============================================================================

/// Query results provider that includes strategy parameter
/// Parameters: {query, strategy}
final queryResultsProvider = FutureProvider.family<
    QueryResponse,
    ({String query, ChunkingStrategy strategy})>(
  (ref, params) async {
    // Validate query
    if (params.query.trim().isEmpty) {
      throw Exception('Please enter a query');
    }

    // Get RAG service and perform query
    final ragService = ref.watch(ragServiceProvider);
    
    try {
      final response = await ragService.queryDocuments(
        query: params.query,
        strategy: params.strategy.value,
        nResults: 5,
        returnParents: true,
      );
      
      return response;
    } catch (e) {
      throw Exception('Query failed: $e');
    }
  },
);

// ============================================================================
// HELPER PROVIDER: Check strategy availability (future use)
// ============================================================================

/// Provider to track which strategies are currently available
/// Useful when you add the health check endpoint
final availableStrategiesProvider = FutureProvider<List<ChunkingStrategy>>((ref) async {
  // For now, return all strategies as available
  // Later, you can call the /health endpoint to check actual availability
  return ChunkingStrategy.values;
});

// ============================================================================
// METRICS PROVIDER (Optional: for comparing strategies)
// ============================================================================

/// Store metrics from queries for comparison
final queryMetricsProvider = StateProvider<Map<String, dynamic>>((ref) => {});

/// Helper to track strategy performance
class StrategyMetrics {
  final String strategy;
  final double avgSimilarity;
  final int resultsCount;
  final Duration queryTime;

  StrategyMetrics({
    required this.strategy,
    required this.avgSimilarity,
    required this.resultsCount,
    required this.queryTime,
  });

  Map<String, dynamic> toJson() => {
    'strategy': strategy,
    'avgSimilarity': avgSimilarity,
    'resultsCount': resultsCount,
    'queryTimeMs': queryTime.inMilliseconds,
  };
}