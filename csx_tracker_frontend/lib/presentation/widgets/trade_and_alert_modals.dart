// lib/presentation/widgets/trade_and_alert_modals.dart
import 'package:flutter/material.dart';
import '../../core/utils/csx_formatter.dart';
import '../../domain/entities/position_entity.dart';
import '../../domain/policies/csx_tick_policy.dart';

class TradeAndAlertModals {
  static const List<String> csxTickers = [
    'ABC',
    'PWSA',
    'PPAP',
    'PAS',
    'PPSP',
    'CGSM',
    'MJQE',
    'PEPC',
    'DBDE',
    'GTI',
    'JSL',
    'PCG'
  ];

  /// Modal to record a BUY or SELL transaction
  static void showTradeModal(
    BuildContext context, {
    required bool isBuy,
    String? initialTicker,
    int? initialPriceKhr,
    required void Function(String ticker, int shares, int priceKhr) onSubmit,
  }) {
    String selectedTicker = initialTicker ?? csxTickers.first;
    final sharesCtrl = TextEditingController();
    final priceCtrl = TextEditingController(
      text: initialPriceKhr != null && initialPriceKhr > 0
          ? initialPriceKhr.toString()
          : '',
    );

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return Padding(
          padding: EdgeInsets.only(
            left: 20,
            right: 20,
            top: 20,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
          ),
          child: StatefulBuilder(
            builder: (context, setModalState) {
              return Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    isBuy
                        ? 'Log CSX Buy Tranche'
                        : 'Log CSX Sale ($selectedTicker)',
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 16),
                  if (initialTicker == null)
                    DropdownButtonFormField<String>(
                      value: selectedTicker,
                      decoration: const InputDecoration(
                        labelText: 'CSX Stock Ticker',
                        border: OutlineInputBorder(),
                      ),
                      items: csxTickers
                          .map(
                              (t) => DropdownMenuItem(value: t, child: Text(t)))
                          .toList(),
                      onChanged: (val) {
                        if (val != null)
                          setModalState(() => selectedTicker = val);
                      },
                    ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: sharesCtrl,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Number of Shares',
                      hintText: 'e.g. 1000',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: priceCtrl,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                      labelText: 'Execution Price (KHR)',
                      hintText: 'e.g. 10000',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 18),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: isBuy
                            ? const Color(0xFF0D1B2A)
                            : Colors.red.shade700,
                        foregroundColor: Colors.white,
                      ),
                      onPressed: () {
                        final shares =
                            int.tryParse(sharesCtrl.text.trim()) ?? 0;
                        final price = int.tryParse(priceCtrl.text.trim()) ?? 0;
                        if (shares > 0 && price > 0) {
                          onSubmit(selectedTicker, shares, price);
                          Navigator.pop(ctx);
                        }
                      },
                      child: Text(isBuy
                          ? 'Save Buy & Calculate Break-Even'
                          : 'Record Sale'),
                    ),
                  ),
                ],
              );
            },
          ),
        );
      },
    );
  }

  /// Modal to configure a Target Net ROI % or Stop-Loss KHR alert with live CSX tick preview
  static void showSetAlertModal(
    BuildContext context, {
    required PositionEntity position,
    required void Function(String triggerType, double targetValue) onSubmit,
  }) {
    String triggerType = 'TARGET_NET_ROI_PCT';
    final valueCtrl = TextEditingController(text: '12');

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return Padding(
          padding: EdgeInsets.only(
            left: 20,
            right: 20,
            top: 20,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
          ),
          child: StatefulBuilder(
            builder: (context, setModalState) {
              final inputVal = double.tryParse(valueCtrl.text.trim()) ?? 0.0;
              final int previewExecKhr = triggerType == 'TARGET_NET_ROI_PCT'
                  ? CSXTickPolicy.previewTargetPriceKhr(
                      avgCostPerShareKhr: position.avgCostPerShareKhr,
                      sellFeeRate: position.sellFeeRate,
                      targetNetRoiPct: inputVal,
                    )
                  : CSXTickPolicy.alignUp(inputVal);

              return Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Arm Exit Trigger • #${position.ticker}',
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Your Tick Break-Even: ${CSXFormatter.formatKhr(position.breakevenKhr)}',
                    style: const TextStyle(color: Colors.grey, fontSize: 13),
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    value: triggerType,
                    decoration: const InputDecoration(
                      labelText: 'Trigger Strategy',
                      border: OutlineInputBorder(),
                    ),
                    items: const [
                      DropdownMenuItem(
                        value: 'TARGET_NET_ROI_PCT',
                        child: Text('Target Net ROI % (After All Fees)'),
                      ),
                      DropdownMenuItem(
                        value: 'TARGET_PRICE_KHR',
                        child: Text('Target Limit Price (KHR)'),
                      ),
                      DropdownMenuItem(
                        value: 'STOP_LOSS_KHR',
                        child: Text('Stop-Loss Floor (KHR)'),
                      ),
                    ],
                    onChanged: (val) {
                      if (val != null) setModalState(() => triggerType = val);
                    },
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: valueCtrl,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    onChanged: (_) => setModalState(() {}),
                    decoration: InputDecoration(
                      labelText: triggerType == 'TARGET_NET_ROI_PCT'
                          ? 'Desired Net Return (%)'
                          : 'Trigger Price (KHR)',
                      border: const OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.blueGrey.shade50,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      'CSX Tick-Aligned Trigger Price: ${CSXFormatter.formatKhr(previewExecKhr)}',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF0D1B2A),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    height: 48,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF0D1B2A),
                        foregroundColor: Colors.white,
                      ),
                      onPressed: () {
                        if (inputVal > 0) {
                          onSubmit(triggerType, inputVal);
                          Navigator.pop(ctx);
                        }
                      },
                      child: const Text('Arm Telegram & Live Exit Alert'),
                    ),
                  ),
                ],
              );
            },
          ),
        );
      },
    );
  }
}
