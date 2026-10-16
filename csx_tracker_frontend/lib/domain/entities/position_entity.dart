// lib/domain/entities/position_entity.dart
import 'package:equatable/equatable.dart';
import '../../core/config/app_config.dart';
import 'exit_alert_entity.dart';

class PositionEntity extends Equatable {
  final int positionId;
  final String ticker;
  final int shares;
  final double totalCostKhr;
  final double avgCostPerShareKhr;
  final int breakevenKhr;
  final int lastPriceKhr;
  final int bestBidKhr;
  final double sellFeeRate;
  final List<ExitAlertEntity> activeAlerts;
  final double fxRate;

  const PositionEntity({
    required this.positionId,
    required this.ticker,
    required this.shares,
    required this.totalCostKhr,
    required this.avgCostPerShareKhr,
    required this.breakevenKhr,
    required this.lastPriceKhr,
    required this.bestBidKhr,
    required this.sellFeeRate,
    this.activeAlerts = const [],
    this.fxRate = AppConfig.defaultFxKhrUsd,
  });

  /// Uses Best Bid for realistic exit liquidity; falls back to Last Traded Price
  int get executableExitPriceKhr => bestBidKhr > 0 ? bestBidKhr : lastPriceKhr;

  double get grossMarketValueKhr =>
      (shares * executableExitPriceKhr).toDouble();

  double get netLiquidationValueKhr =>
      grossMarketValueKhr * (1.0 - sellFeeRate);

  double get netProfitKhr => netLiquidationValueKhr - totalCostKhr;

  double get netProfitUsd => netProfitKhr / fxRate;

  double get netRoiPct =>
      totalCostKhr > 0 ? (netProfitKhr / totalCostKhr) * 100.0 : 0.0;

  bool get isProfitable => netProfitKhr >= 0;

  int? get primaryTargetPriceKhr =>
      activeAlerts.isNotEmpty ? activeAlerts.first.targetExecPriceKhr : null;

  /// Progress (0.0 to 1.0) from Break-Even toward the primary Exit Target
  double get progressToTarget {
    final target = primaryTargetPriceKhr;
    if (target == null || target <= breakevenKhr)
      return isProfitable ? 1.0 : 0.0;
    final progress =
        (executableExitPriceKhr - breakevenKhr) / (target - breakevenKhr);
    return progress.clamp(0.0, 1.0);
  }

  PositionEntity copyWithLiveQuote({
    int? lastPriceKhr,
    int? bestBidKhr,
  }) {
    return PositionEntity(
      positionId: positionId,
      ticker: ticker,
      shares: shares,
      totalCostKhr: totalCostKhr,
      avgCostPerShareKhr: avgCostPerShareKhr,
      breakevenKhr: breakevenKhr,
      lastPriceKhr: lastPriceKhr ?? this.lastPriceKhr,
      bestBidKhr: bestBidKhr ?? this.bestBidKhr,
      sellFeeRate: sellFeeRate,
      activeAlerts: activeAlerts,
      fxRate: fxRate,
    );
  }

  @override
  List<Object?> get props => [
        positionId,
        ticker,
        shares,
        totalCostKhr,
        breakevenKhr,
        lastPriceKhr,
        bestBidKhr,
        sellFeeRate,
        activeAlerts,
      ];
}
