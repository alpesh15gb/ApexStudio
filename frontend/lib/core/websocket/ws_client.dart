import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../config/app_config.dart';

final wsClientProvider = Provider<WebSocketClient>((ref) => WebSocketClient());

class WebSocketClient {
  WebSocketChannel? _channel;
  final _messageController = StreamController<Map<String, dynamic>>.broadcast();
  Timer? _reconnectTimer;
  bool _isConnected = false;

  Stream<Map<String, dynamic>> get messages => _messageController.stream;
  bool get isConnected => _isConnected;

  void connect(String projectId) {
    final wsBase = AppConfig.wsUrl.isEmpty
        ? '${Uri.base.scheme == "https" ? "wss" : "ws"}://${Uri.base.host}'
        : AppConfig.wsUrl;
    final uri = Uri.parse('$wsBase/ws/chat/$projectId');
    _channel = WebSocketChannel.connect(uri);
    _isConnected = true;

    _channel!.stream.listen(
      (data) {
        try {
          final message = jsonDecode(data as String) as Map<String, dynamic>;
          _messageController.add(message);
        } catch (_) {}
      },
      onDone: () {
        _isConnected = false;
        _scheduleReconnect(projectId);
      },
      onError: (_) {
        _isConnected = false;
        _scheduleReconnect(projectId);
      },
    );
  }

  void _scheduleReconnect(String projectId) {
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 3), () => connect(projectId));
  }

  void send(Map<String, dynamic> message) {
    if (_channel != null && _isConnected) {
      _channel!.sink.add(jsonEncode(message));
    }
  }

  void disconnect() {
    _reconnectTimer?.cancel();
    _channel?.sink.close();
    _isConnected = false;
  }

  void dispose() {
    disconnect();
    _messageController.close();
  }
}
