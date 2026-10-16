// lib/data/models/position_model.dart
import '../../domain/entities/exit_alert_entity.dart';
import '../../domain/entities/position_entity.dart';

class ExitAlertModel extends ExitAlertEntity {
  const ExitAlertModel({
    required super.alertId,
    required super.triggerType,
    required super.targetValue,
    required super.targetExecPriceKhr,
  });

  factory ExitAlertModel.fromJson(Map<String, dynamic> json) {
    return ExitAlertModel(
      alertId: (json['alert_id'] as num).toInt(),
      triggerType: json['trigger_type'] as String,
      targetValue: (json['target_value'] as num).toDouble(),
      targetExecPriceKhr: (json['target_exec_price_khr'] as num).toInt(),
    );
  }
}

class PositionModel extends PositionEntity {
  const PositionModel({
    required super.positionId,
    required super.ticker,
    required super.shares,
    required super.totalCostKhr,
    required super.avgCostPerShareKhr,
    required super.breakevenKhr,
    required super.lastPriceKhr,
    required super.bestBidKhr,
    required super.sellFeeRate,
    required super.activeAlerts,
  });

  factory PositionModel.fromJson(Map<String, dynamic> json) {
    final alertsRaw = json['active_alerts'] as List<dynamic>? ?? [];
    return PositionModel(
      positionId: (json['position_id'] as num).toInt(),
      ticker: json['ticker'] as String,
      shares: (json['shares'] as num).toInt(),
      totalCostKhr: (json['total_cost_khr'] as num).toDouble(),
      avgCostPerShareKhr: (json['avg_cost_per_share_khr'] as num).toDouble(),
      breakevenKhr: (json['breakeven_khr'] as num).toInt(),
      lastPriceKhr: (json['last_price_khr'] as num).toInt(),
      bestBidKhr:
          (json['best_bid_khr'] as num? ?? json['last_price_khr'] as num)
              .toInt(),
      sellFeeRate: (json['sell_fee_rate'] as num? ?? 0.005).toDouble(),
      activeAlerts: alertsRaw
          .map((a) => ExitAlertModel.fromJson(a as Map<String, dynamic>))
          .toList(),
    );
  }
}
