// lib/data/repositories/portfolio_repository_impl.dart
import 'package:frontend/data/datasources/csx_websocket_datasource.dart';
import 'package:frontend/data/datasources/portfolio_remote_datasource.dart';

import '../../domain/entities/position_entity.dart';
import '../../domain/entities/ws_event_entity.dart';
import '../../domain/repositories/i_portfolio_repository.dart';

class PortfolioRepositoryImpl implements IPortfolioRepository {
  final PortfolioRemoteDataSource _remoteDataSource;
  final CSXWebSocketDataSource _wsDataSource;

  PortfolioRepositoryImpl({
    required PortfolioRemoteDataSource remoteDataSource,
    required CSXWebSocketDataSource wsDataSource,
  })  : _remoteDataSource = remoteDataSource,
        _wsDataSource = wsDataSource;

  @override
  Stream<CSXWebSocketEvent> get marketEventsStream => _wsDataSource.events;

  @override
  Future<List<PositionEntity>> fetchPortfolio(int telegramChatId) {
    return _remoteDataSource.getPortfolio(telegramChatId);
  }

  @override
  Future<void> recordBuy({
    required int telegramChatId,
    required String ticker,
    required int shares,
    required int priceKhr,
  }) {
    return _remoteDataSource.postBuy(
      telegramChatId: telegramChatId,
      ticker: ticker,
      shares: shares,
      priceKhr: priceKhr,
    );
  }

  @override
  Future<void> recordSell({
    required int telegramChatId,
    required String ticker,
    required int shares,
    required int priceKhr,
  }) {
    return _remoteDataSource.postSell(
      telegramChatId: telegramChatId,
      ticker: ticker,
      shares: shares,
      priceKhr: priceKhr,
    );
  }

  @override
  Future<void> createExitAlert({
    required int telegramChatId,
    required String ticker,
    required String triggerType,
    required double targetValue,
  }) {
    return _remoteDataSource.postAlert(
      telegramChatId: telegramChatId,
      ticker: ticker,
      triggerType: triggerType,
      targetValue: targetValue,
    );
  }

  @override
  void dispose() {
    _wsDataSource.dispose();
  }
}
