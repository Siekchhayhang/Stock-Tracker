// lib/data/datasources/csx_websocket_datasource.dart
import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../core/config/app_config.dart';
import '../../domain/entities/ws_event_entity.dart';

class CSXWebSocketDataSource {
  final String _wsUrl;
  WebSocketChannel? _channel;
  StreamSubscription? _subscription;
  Timer? _reconnectTimer;
  bool _isDisposed = false;

  final StreamController<CSXWebSocketEvent> _eventController =
      StreamController<CSXWebSocketEvent>.broadcast();

  CSXWebSocketDataSource({String wsUrl = AppConfig.wsUrl}) : _wsUrl = wsUrl {
    _connect();
  }

  Stream<CSXWebSocketEvent> get events => _eventController.stream;

  void _connect() {
    if (_isDisposed) return;
    try {
      _channel = WebSocketChannel.connect(Uri.parse(_wsUrl));
      _subscription = _channel!.stream.listen(
        _onRawMessage,
        onError: (_) => _scheduleReconnect(),
        onDone: _scheduleReconnect,
      );
    } catch (_) {
      _scheduleReconnect();
    }
  }

  void _onRawMessage(dynamic raw) {
    try {
      final decoded = jsonDecode(raw as String) as Map<String, dynamic>;
      final eventType = decoded['event'] as String?;

      if (eventType == 'PRICE_UPDATE') {
        final data = decoded['data'] as Map<String, dynamic>;
        final Map<String, LiveQuoteTick> parsedTicks = {};

        data.forEach((ticker, quoteMap) {
          if (quoteMap is Map<String, dynamic>) {
            parsedTicks[ticker] = LiveQuoteTick(
              lastPriceKhr: (quoteMap['last_price_khr'] as num).toInt(),
              bestBidKhr: (quoteMap['best_bid_khr'] as num? ??
                      quoteMap['last_price_khr'] as num)
                  .toInt(),
              volume: (quoteMap['volume'] as num? ?? 0).toInt(),
            );
          } else if (quoteMap is num) {
            parsedTicks[ticker] = LiveQuoteTick(
              lastPriceKhr: quoteMap.toInt(),
              bestBidKhr: quoteMap.toInt(),
              volume: 0,
            );
          }
        });

        _eventController.add(PriceUpdateWsEvent(parsedTicks));
      } else if (eventType == 'EXIT_ALERT_TRIGGERED') {
        final data = decoded['data'] as Map<String, dynamic>;
        _eventController.add(
          ExitAlertTriggeredWsEvent(
            positionId: (data['position_id'] as num).toInt(),
            ticker: data['ticker'] as String,
            triggerType: data['trigger_type'] as String,
            executablePriceKhr: (data['executable_price_khr'] as num).toInt(),
            netProfitKhr: (data['net_profit_khr'] as num).toInt(),
            netRoiPct: (data['net_roi_pct'] as num).toDouble(),
          ),
        );
      }
    } catch (_) {
      // Ignore malformed frames
    }
  }

  void _scheduleReconnect() {
    if (_isDisposed) return;
    _subscription?.cancel();
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 5), _connect);
  }

  void dispose() {
    _isDisposed = true;
    _reconnectTimer?.cancel();
    _subscription?.cancel();
    _channel?.sink.close();
    _eventController.close();
  }
}
