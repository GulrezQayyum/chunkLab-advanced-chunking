// Simple data models WITHOUT Freezed (no build_runner needed)

class ChunkResult {
  final String chunkId;
  final String text;
  final double similarityScore;
  final String chunkType;
  final ParentContext? parentContext;
  final Map<String, dynamic> metadata;

  ChunkResult({
    required this.chunkId,
    required this.text,
    required this.similarityScore,
    required this.chunkType,
    this.parentContext,
    required this.metadata,
  });

  factory ChunkResult.fromJson(Map<String, dynamic> json) {
    return ChunkResult(
      chunkId: json['chunk_id'] ?? '',
      text: json['text'] ?? '',
      similarityScore: (json['similarity_score'] ?? 0).toDouble(),
      chunkType: json['chunk_type'] ?? '',
      parentContext: json['parent_context'] != null
          ? ParentContext.fromJson(json['parent_context'])
          : null,
      metadata: json['metadata'] ?? {},
    );
  }
}

class ParentContext {
  final String text;
  final Map<String, dynamic> metadata;

  ParentContext({required this.text, required this.metadata});

  factory ParentContext.fromJson(Map<String, dynamic> json) {
    return ParentContext(
      text: json['text'] ?? '',
      metadata: json['metadata'] ?? {},
    );
  }
}

class QueryResponse {
  final String query;
  final List<ChunkResult> results;
  final String strategy;
  final int totalResults; // 👈 added from backend
  final Map<String, dynamic>? metrics; // 👈 now a map, optional

  QueryResponse({
    required this.query,
    required this.results,
    required this.strategy,
    required this.totalResults,
    this.metrics,
  });

  
  factory QueryResponse.fromJson(Map<String, dynamic> json) {
    return QueryResponse(
      query: json['query'] ?? '',
      results: (json['results'] as List<dynamic>?)
              ?.map((e) => ChunkResult.fromJson(e as Map<String, dynamic>))
              .toList() ?? [],
      strategy: json['strategy'] ?? '',
      totalResults: json['total_results'] ?? 0,
      metrics: json['metrics'] as Map<String, dynamic>?, // may be null
    );
  }
}
