// lib/domain/entities/exit_alert_entity.dart
import 'package:equatable/equatable.dart';

class ExitAlertEntity extends Equatable {
  final int alertId;
  final String
      triggerType; // 'TARGET_NET_ROI_PCT', 'TARGET_PRICE_KHR', 'STOP_LOSS_KHR'
  final double targetValue;
  final int targetExecPriceKhr;

  const ExitAlertEntity({
    required this.alertId,
    required this.triggerType,
    required this.targetValue,
    required this.targetExecPriceKhr,
  });

  @override
  List<Object?> get props =>
      [alertId, triggerType, targetValue, targetExecPriceKhr];
}
