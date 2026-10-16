// lib/presentation/state/portfolio_state.dart
import 'package:equatable/equatable.dart';
import '../../core/config/app_config.dart';
import '../../domain/entities/position_entity.dart';
import '../../domain/entities/ws_event_entity.dart';

enum PortfolioStatus { initial, loading, loaded, error }

class PortfolioState extends Equatable {
  final PortfolioStatus status;
  final List<PositionEntity> positions;
  final String? errorMessage;
  final ExitAlertTriggeredWsEvent? latestTriggeredAlert;

  const PortfolioState({
    this.status = PortfolioStatus.initial,
    this.positions = const [],
    this.errorMessage,
    this.latestTriggeredAlert,
  });

  double get totalCostKhr =>
      positions.fold(0.0, (sum, item) => sum + item.totalCostKhr);

  double get totalNetLiquidationKhr =>
      positions.fold(0.0, (sum, item) => sum + item.netLiquidationValueKhr);

  double get totalNetProfitKhr => totalNetLiquidationKhr - totalCostKhr;

  double get totalNetProfitUsd => totalNetProfitKhr / AppConfig.defaultFxKhrUsd;

  double get totalNetRoiPct =>
      totalCostKhr > 0 ? (totalNetProfitKhr / totalCostKhr) * 100.0 : 0.0;

  PortfolioState copyWith({
    PortfolioStatus? status,
    List<PositionEntity>? positions,
    String? errorMessage,
    ExitAlertTriggeredWsEvent? latestTriggeredAlert,
    bool clearError = false,
  }) {
    return PortfolioState(
      status: status ?? this.status,
      positions: positions ?? this.positions,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
      latestTriggeredAlert: latestTriggeredAlert ?? this.latestTriggeredAlert,
    );
  }

  @override
  List<Object?> get props => [
        status,
        positions,
        errorMessage,
        latestTriggeredAlert,
      ];
}
