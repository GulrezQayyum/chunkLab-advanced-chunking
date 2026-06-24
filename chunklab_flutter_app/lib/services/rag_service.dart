import 'package:chunklab_flutter_app/models/chunk_result.dart';
import 'package:dio/dio.dart';
import '../config/constants.dart';
import '../models/query_response.dart';

class RagService {
  final Dio _dio;

  RagService({Dio? dio})
    : _dio =
          dio ??
          Dio(
            BaseOptions(
              baseUrl: AppConstants.apiBaseUrl,
              connectTimeout: AppConstants.apiTimeout,
              receiveTimeout: AppConstants.apiTimeout,
            ),
          );

  Future<QueryResponse> queryDocuments({
    required String query,
    int nResults = 5,
    bool returnParents = true,
  }) async {
    try {
      final response = await _dio.post(
        AppConstants.queryEndpoint,
        data: {
          'query': query,
          'n_results': nResults,
          'return_parents': returnParents,
        },
      );

      return QueryResponse.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleDioError(e);
    }
  }

  String _handleDioError(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
        return 'Connection timeout. Check if server is running.';
      case DioExceptionType.receiveTimeout:
        return 'Server took too long to respond.';
      case DioExceptionType.connectionError:
        return 'Cannot connect to localhost:8001. Ensure FastAPI server is running.';
      case DioExceptionType.badResponse:
        return 'Server error: ${e.response?.statusCode}';
      default:
        return 'Error: ${e.message}';
    }
  }
}
