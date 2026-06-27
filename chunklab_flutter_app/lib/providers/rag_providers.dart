import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/rag_service.dart';
import '../models/query_models.dart';  
// Service provider
final ragServiceProvider = Provider<RagService>((ref) {
  return RagService();
});

// Current query text
final queryTextProvider = StateProvider<String>((ref) => '');

// Query results (triggered manually, not auto)
final queryResultsProvider =
    FutureProvider.family<QueryResponse, String>((ref, query) async {
  if (query.trim().isEmpty) {
    throw 'Please enter a query';
  }

  final ragService = ref.watch(ragServiceProvider);
  return ragService.queryDocuments(query: query);
});