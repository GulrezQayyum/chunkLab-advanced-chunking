import 'package:dio/dio.dart';
import '../config/constants.dart';
import '../models/query_models.dart';

class RagService {
  late final Dio _dio;

  RagService() {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        connectTimeout: AppConstants.apiTimeout,
        receiveTimeout: AppConstants.apiTimeout,
        headers: {'Content-Type': 'application/json'},
      ),
    );
  }

  Future<QueryResponse> queryDocuments({
    required String query,
    int nResults = 5,
    bool returnParents = true,
  }) async {
    try {
      // IMPORTANT: Send as query parameters, not JSON body
      final response = await _dio.post(
        AppConstants.queryEndpoint,
        queryParameters: {
          'query': query,
          'n_results': nResults,
          'return_parents': returnParents,
        },
      );

      return QueryResponse.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _handleDioError(e);
    } catch (e) {
      throw 'Unexpected error: $e';
    }
  }

  String _handleDioError(DioException e) {
    if (e.type == DioExceptionType.connectionTimeout) {
      return 'Connection timeout. Is localhost:8001 running?';
    } else if (e.type == DioExceptionType.receiveTimeout) {
      return 'Server took too long to respond.';
    } else if (e.type == DioExceptionType.connectionError) {
      return 'Cannot connect to localhost:8001. Start the FastAPI server.';
    } else if (e.type == DioExceptionType.badResponse) {
      return 'Server error: ${e.response?.statusCode} - ${e.response?.data}';
    } else {
      return 'Error: ${e.message}';
    }
  }
}