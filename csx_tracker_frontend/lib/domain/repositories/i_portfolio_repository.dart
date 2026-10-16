// lib/domain/repositories/i_portfolio_repository.dart
import '../entities/position_entity.dart';
import '../entities/ws_event_entity.dart';

abstract class IPortfolioRepository {
  Stream<CSXWebSocketEvent> get marketEventsStream;

  Future<List<PositionEntity>> fetchPortfolio(int telegramChatId);

  Future<void> recordBuy({
    required int telegramChatId,
    required String ticker,
    required int shares,
    required int priceKhr,
  });

  Future<void> recordSell({
    required int telegramChatId,
    required String ticker,
    required int shares,
    required int priceKhr,
  });

  Future<void> createExitAlert({
    required int telegramChatId,
    required String ticker,
    required String triggerType,
    required double targetValue,
  });

  void dispose();
}
