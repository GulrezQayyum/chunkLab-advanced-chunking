/// Models for query responses from the RAG backend.

class ChunkResult {
  final String id;          // matches backend 'id'
  final String text;
  final double similarityScore;  // backend field name is 'similarity'
  final Map<String, dynamic> metadata;
  final ParentContext? parentContext; // optional, used if backend returns it

  ChunkResult({
    required this.id,
    required this.text,
    required this.similarityScore,
    required this.metadata,
    this.parentContext,
  });

  factory ChunkResult.fromJson(Map<String, dynamic> json) {
    return ChunkResult(
      id: json['id'] ?? '',
      text: json['text'] ?? '',
      similarityScore: (json['similarity'] ?? 0).toDouble(),
      metadata: json['metadata'] ?? {},
      parentContext: json['parent_context'] != null
          ? ParentContext.fromJson(json['parent_context'])
          : null,
    );
  }
}

class ParentContext {
  final String text;
  final Map<String, dynamic> metadata;

  ParentContext({
    required this.text,
    required this.metadata,
  });

  factory ParentContext.fromJson(Map<String, dynamic> json) {
    return ParentContext(
      text: json['text'] ?? '',
      metadata: json['metadata'] ?? {},
    );
  }
}

class QueryResponse {
  final String strategy;
  final String query;
  final List<ChunkResult> results;
  final int totalResults;
  final Map<String, dynamic>? metrics; // optional, contains avg_similarity etc.

  QueryResponse({
    required this.strategy,
    required this.query,
    required this.results,
    required this.totalResults,
    this.metrics,
  });

  factory QueryResponse.fromJson(Map<String, dynamic> json) {
    return QueryResponse(
      strategy: json['strategy'] ?? '',
      query: json['query'] ?? '',
      results: (json['results'] as List<dynamic>?)
              ?.map((e) => ChunkResult.fromJson(e as Map<String, dynamic>))
              .toList() ?? [],
      totalResults: json['total_results'] ?? 0,
      metrics: json['metrics'] as Map<String, dynamic>?, // may be null
    );
  }
}