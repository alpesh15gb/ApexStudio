class AppConfig {
  static const String appName = 'Apex Studio';

  // Use relative URLs so API calls go to the same host serving the frontend.
  // For development, override: --dart-define=API_URL=http://localhost:8002
  static const String apiUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: '',
  );
  static const String wsUrl = String.fromEnvironment(
    'WS_URL',
    defaultValue: '',
  );
  static const int connectionTimeout = 30;
  static const Duration debounceDuration = Duration(milliseconds: 300);
}
