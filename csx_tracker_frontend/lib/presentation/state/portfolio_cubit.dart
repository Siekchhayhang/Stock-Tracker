// lib/presentation/state/portfolio_cubit.dart
import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../domain/entities/ws_event_entity.dart';
import '../../domain/repositories/i_portfolio_repository.dart';
import 'portfolio_state.dart';

class PortfolioCubit extends Cubit<PortfolioState> {
  final IPortfolioRepository _repository;
  final int telegramChatId;
  StreamSubscription<CSXWebSocketEvent>? _wsSubscription;

  PortfolioCubit({
    required IPortfolioRepository repository,
    required this.telegramChatId,
  })  : _repository = repository,
        super(const PortfolioState()) {
    _wsSubscription = _repository.marketEventsStream.listen(_onMarketEvent);
  }

  Future<void> loadPortfolio() async {
    emit(state.copyWith(status: PortfolioStatus.loading, clearError: true));
    try {
      final positions = await _repository.fetchPortfolio(telegramChatId);
      emit(state.copyWith(
        status: PortfolioStatus.loaded,
        positions: positions,
      ));
    } catch (e) {
      emit(state.copyWith(
        status: PortfolioStatus.error,
        errorMessage: e.toString(),
      ));
    }
  }

  void _onMarketEvent(CSXWebSocketEvent event) {
    if (event is PriceUpdateWsEvent) {
      final updatedPositions = state.positions.map((pos) {
        final tick = event.ticks[pos.ticker];
        if (tick != null) {
          return pos.copyWithLiveQuote(
            lastPriceKhr: tick.lastPriceKhr,
            bestBidKhr: tick.bestBidKhr,
          );
        }
        return pos;
      }).toList();

      emit(state.copyWith(positions: updatedPositions));
    } else if (event is ExitAlertTriggeredWsEvent) {
      emit(state.copyWith(latestTriggeredAlert: event));
      loadPortfolio(); // Refresh active alerts state from DB
    }
  }

  Future<void> submitBuy({
    required String ticker,
    required int shares,
    required int priceKhr,
  }) async {
    try {
      await _repository.recordBuy(
        telegramChatId: telegramChatId,
        ticker: ticker,
        shares: shares,
        priceKhr: priceKhr,
      );
      await loadPortfolio();
    } catch (e) {
      emit(state.copyWith(errorMessage: e.toString()));
    }
  }

  Future<void> submitSell({
    required String ticker,
    required int shares,
    required int priceKhr,
  }) async {
    try {
      await _repository.recordSell(
        telegramChatId: telegramChatId,
        ticker: ticker,
        shares: shares,
        priceKhr: priceKhr,
      );
      await loadPortfolio();
    } catch (e) {
      emit(state.copyWith(errorMessage: e.toString()));
    }
  }

  Future<void> submitExitAlert({
    required String ticker,
    required String triggerType,
    required double targetValue,
  }) async {
    try {
      await _repository.createExitAlert(
        telegramChatId: telegramChatId,
        ticker: ticker,
        triggerType: triggerType,
        targetValue: targetValue,
      );
      await loadPortfolio();
    } catch (e) {
      emit(state.copyWith(errorMessage: e.toString()));
    }
  }

  @override
  Future<void> close() {
    _wsSubscription?.cancel();
    return super.close();
  }
}
