import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/rag_service.dart';
import '../models/query_response.dart';

final ragServiceProvider = Provider<RagService>((ref) => RagService());

final queryInputProvider = StateProvider<String>((ref) => '');

final queryResultsProvider =
    FutureProvider.autoDispose.family<QueryResponse, String>((ref, query) async {
  if (query.isEmpty) {
    throw Exception('Query cannot be empty');
  }

 
  final ragService = ref.watch(ragServiceProvider);
  return ragService.queryDocuments(query: query);
});
