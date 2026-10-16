// lib/domain/entities/ws_event_entity.dart
sealed class CSXWebSocketEvent {
  const CSXWebSocketEvent();
}

class LiveQuoteTick {
  final int lastPriceKhr;
  final int bestBidKhr;
  final int volume;

  const LiveQuoteTick({
    required this.lastPriceKhr,
    required this.bestBidKhr,
    required this.volume,
  });
}

class PriceUpdateWsEvent extends CSXWebSocketEvent {
  final Map<String, LiveQuoteTick> ticks;
  const PriceUpdateWsEvent(this.ticks);
}

class ExitAlertTriggeredWsEvent extends CSXWebSocketEvent {
  final int positionId;
  final String ticker;
  final String triggerType;
  final int executablePriceKhr;
  final int netProfitKhr;
  final double netRoiPct;

  const ExitAlertTriggeredWsEvent({
    required this.positionId,
    required this.ticker,
    required this.triggerType,
    required this.executablePriceKhr,
    required this.netProfitKhr,
    required this.netRoiPct,
  });
}
