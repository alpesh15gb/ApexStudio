import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../api/api_client.dart';

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.read(apiClientProvider));
});

class AuthState {
  final bool isAuthenticated;
  final String? token;
  final String? email;
  final bool isLoading;
  final String? error;

  const AuthState({
    this.isAuthenticated = false,
    this.token,
    this.email,
    this.isLoading = false,
    this.error,
  });

  AuthState copyWith({
    bool? isAuthenticated,
    String? token,
    String? email,
    bool? isLoading,
    String? error,
  }) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      token: token ?? this.token,
      email: email ?? this.email,
      isLoading: isLoading ?? this.isLoading,
      error: error,
    );
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  final ApiClient _api;

  AuthNotifier(this._api) : super(const AuthState());

  Future<void> login(String email, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await _api.login(email, password);
      final token = response.data['access_token'] as String;
      _api.dio.options.headers['Authorization'] = 'Bearer $token';
      state = AuthState(
        isAuthenticated: true,
        token: token,
        email: email,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Login failed: $e');
      rethrow;
    }
  }

  Future<void> register(String email, String password, String fullName) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final response = await _api.register(email, password, fullName);
      final token = response.data['access_token'] as String;
      _api.dio.options.headers['Authorization'] = 'Bearer $token';
      state = AuthState(
        isAuthenticated: true,
        token: token,
        email: email,
      );
    } catch (e) {
      state = state.copyWith(isLoading: false, error: 'Registration failed: $e');
      rethrow;
    }
  }

  void logout() {
    _api.dio.options.headers.remove('Authorization');
    state = const AuthState();
  }
}
