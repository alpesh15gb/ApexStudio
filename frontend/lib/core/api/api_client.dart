import 'package:dio/dio.dart';
import '../config/app_config.dart';

class ApiClient {
  late final Dio _dio;

  ApiClient() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConfig.apiUrl.isNotEmpty ? '${AppConfig.apiUrl}/api/v1' : '/api/v1',
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        final token = _getToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (error, handler) {
        if (error.response?.statusCode == 401) {
          // Token expired — redirect to login
        }
        return handler.next(error);
      },
    ));
  }

  String? _getToken() {
    // TODO: Load from secure storage
    return null;
  }

  Future<Response> get(String path, {Map<String, dynamic>? params}) =>
      _dio.get(path, queryParameters: params);

  Future<Response> post(String path, {dynamic data}) =>
      _dio.post(path, data: data);

  Future<Response> put(String path, {dynamic data}) =>
      _dio.put(path, data: data);

  Future<Response> patch(String path, {dynamic data}) =>
      _dio.patch(path, data: data);

  Future<Response> delete(String path) => _dio.delete(path);

  // Auth
  Future<Response> login(String email, String password) =>
      _dio.post('/auth/login', data: {'email': email, 'password': password});

  Future<Response> register(String email, String password, String fullName) =>
      _dio.post('/auth/register', data: {
        'email': email,
        'password': password,
        'full_name': fullName,
      });

  // Projects
  Future<Response> getProjects(String workspaceId) =>
      _dio.get('/projects', queryParameters: {'workspace_id': workspaceId});

  Future<Response> createProject(String workspaceId, String name, String description) =>
      _dio.post('/projects', queryParameters: {'workspace_id': workspaceId}, data: {
        'name': name,
        'description': description,
      });

  // AI Chat
  Future<Response> sendChatMessage(String projectId, String message) =>
      _dio.post('/ai/chat', data: {'project_id': projectId, 'message': message});

  // Auth token management
  void setToken(String token) {
    _dio.options.headers['Authorization'] = 'Bearer $token';
  }

  void clearToken() {
    _dio.options.headers.remove('Authorization');
  }

  // Workspace
  Future<Response> startWorkspace(String projectId) =>
      _dio.post('/workspace-runtime/$projectId/start');

  Future<Response> stopWorkspace(String projectId) =>
      _dio.post('/workspace-runtime/$projectId/stop');

  Future<Response> getWorkspaceStatus(String projectId) =>
      _dio.get('/workspace-runtime/$projectId/status');
}
