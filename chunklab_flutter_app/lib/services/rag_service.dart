import 'package:dio/dio.dart';
import 'package:chunklab_flutter_app/config/constants.dart';
import 'package:chunklab_flutter_app/models/query_models.dart';

class RAGService {
  late final Dio _dio;

  RAGService() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        connectTimeout: const Duration(seconds: 5),
        receiveTimeout: const Duration(seconds: 10),
        contentType: Headers.jsonContentType,
        responseType: ResponseType.json,
      ),
    );

    // Add logging interceptor
    _dio.interceptors.add(
      LoggingInterceptor(),
    );
  }

  /// Query documents with specified chunking strategy
  ///
  /// Parameters:
  ///   - query: The search query text
  ///   - strategy: Chunking strategy ('fixed_size', 'parent_child', 'semantic', 'hierarchical')
  ///   - nResults: Number of results to return (default: 5)
  ///   - returnParents: Include parent context (default: true)
  ///
  /// Returns: QueryResponse with results and metrics
  /// 
  /// Throws: Exception if query fails
  Future<QueryResponse> queryDocuments({
    required String query,
    String strategy = 'parent_child',
    int nResults = 5,
    bool returnParents = true,
  }) async {
    try {
      print('🔍 RAGService: Querying with strategy=$strategy');
      print('   Query: "$query"');

      final response = await _dio.post(
        AppConstants.queryEndpoint,
        queryParameters: {
          // Strategy as query parameter
          'strategy': strategy,
          'n_results': nResults,
          'return_parents': returnParents,
        },
        data: {
          'query': query,
          'n_results': nResults,
          'return_parents': returnParents,
        },
      );

      print('   ✓ Response status: ${response.statusCode}');
      
      // Parse response
      final queryResponse = QueryResponse.fromJson(
        response.data as Map<String, dynamic>,
      );

      print('   ✓ Received ${queryResponse.results.length} results');
      print('   • Avg similarity: ${queryResponse.metrics?['avg_similarity']?.toStringAsFixed(3) ?? 'N/A'}');

      return queryResponse;
    } on DioException catch (e) {
      print('❌ DioException: ${e.message}');
      throw _handleDioError(e);
    } catch (e) {
      print('❌ Unexpected error: $e');
      throw Exception('Failed to query documents: $e');
    }
  }

  /// Check backend health and available strategies
  /// Useful for verifying which chunking strategies are ready
  Future<Map<String, dynamic>> getHealth() async {
    try {
      final response = await _dio.get('/api/documents/health');
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  /// Get list of available strategies and their collection sizes
  Future<Map<String, dynamic>> listStrategies() async {
    try {
      final response = await _dio.get('/api/documents/strategies');
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  /// Handle Dio errors with meaningful messages
  String _handleDioError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
        return 'Connection timeout. Is the backend running on ${AppConstants.apiBaseUrl}?';
      case DioExceptionType.sendTimeout:
        return 'Send timeout. Request took too long.';
      case DioExceptionType.receiveTimeout:
        return 'Receive timeout. No response from server.';
      case DioExceptionType.badResponse:
        final statusCode = error.response?.statusCode;
        final message = error.response?.data?['detail'] ?? 'Unknown error';
        return 'Server error ($statusCode): $message';
      case DioExceptionType.cancel:
        return 'Request cancelled.';
      case DioExceptionType.unknown:
        return 'Network error: ${error.error}';
      default:
        return 'Error: ${error.message}';
    }
  }
}

/// Logging interceptor for debugging
class LoggingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    print('➡️  REQUEST: ${options.method} ${options.path}');
    print('   Query params: ${options.queryParameters}');
    super.onRequest(options, handler);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    print('⬅️  RESPONSE: ${response.statusCode}');
    super.onResponse(response, handler);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    print('⚠️  ERROR: ${err.type} - ${err.message}');
    super.onError(err, handler);
  }
}