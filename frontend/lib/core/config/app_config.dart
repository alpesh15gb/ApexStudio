class AppConfig {
  static const String appName = 'Apex Studio';
  static const String apiUrl = String.fromEnvironment(
    'API_URL',
    defaultValue: 'http://localhost:8000',
  );
  static const String wsUrl = String.fromEnvironment(
    'WS_URL',
    defaultValue: 'ws://localhost:8000',
  );
  static const int connectionTimeout = 30;
  static const Duration debounceDuration = Duration(milliseconds: 300);
}
