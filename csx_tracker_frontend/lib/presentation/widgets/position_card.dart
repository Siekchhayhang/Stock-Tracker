// lib/presentation/widgets/position_card.dart
import 'package:flutter/material.dart';
import '../../core/utils/csx_formatter.dart';
import '../../domain/entities/position_entity.dart';

class PositionCard extends StatelessWidget {
  final PositionEntity position;
  final VoidCallback onSellTap;
  final VoidCallback onSetAlertTap;

  const PositionCard({
    super.key,
    required this.position,
    required this.onSellTap,
    required this.onSetAlertTap,
  });

  @override
  Widget build(BuildContext context) {
    final isProfitable = position.isProfitable;
    final statusColor =
        isProfitable ? Colors.green.shade700 : Colors.red.shade700;
    final targetKhr = position.primaryTargetPriceKhr;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
      elevation: 1.5,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header Row: Ticker, Shares, and Net ROI Badge
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: const Color(0xFF0D1B2A),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        position.ticker,
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 15,
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Text(
                      '${position.shares} shares',
                      style: const TextStyle(
                        fontSize: 14,
                        color: Colors.black87,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ],
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: statusColor.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${CSXFormatter.formatPct(position.netRoiPct)} Net',
                    style: TextStyle(
                      color: statusColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                    ),
                  ),
                ),
              ],
            ),
            const Divider(height: 24),

            // 3-Column Metrics: Executable Bid, Tick Break-Even, Active Exit Target
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _metricBlock(
                  'Executable Bid',
                  CSXFormatter.formatKhr(position.executableExitPriceKhr),
                ),
                _metricBlock(
                  'Tick Break-Even',
                  CSXFormatter.formatKhr(position.breakevenKhr),
                ),
                _metricBlock(
                  'Exit Target',
                  targetKhr != null
                      ? CSXFormatter.formatKhr(targetKhr)
                      : 'Not Armed',
                  highlight: targetKhr != null,
                ),
              ],
            ),

            if (targetKhr != null) ...[
              const SizedBox(height: 12),
              ClipRRect(
                borderRadius: BorderRadius.circular(6),
                child: LinearProgressIndicator(
                  value: position.progressToTarget,
                  minHeight: 6,
                  backgroundColor: Colors.grey.shade200,
                  valueColor: AlwaysStoppedAnimation<Color>(statusColor),
                ),
              ),
            ],

            const SizedBox(height: 14),

            // Bottom Row: Net P&L in KHR/USD & Quick Actions
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    'Net P&L: ${CSXFormatter.formatKhr(position.netProfitKhr, signed: true)} '
                    '(${CSXFormatter.formatUsd(position.netProfitUsd, signed: true)})',
                    style: TextStyle(
                      color: statusColor,
                      fontWeight: FontWeight.w700,
                      fontSize: 13.5,
                    ),
                  ),
                ),
                TextButton.icon(
                  onPressed: onSetAlertTap,
                  icon:
                      const Icon(Icons.notifications_active_outlined, size: 17),
                  label: const Text('Target'),
                ),
                TextButton.icon(
                  onPressed: onSellTap,
                  icon: const Icon(Icons.sell_outlined, size: 17),
                  label: const Text('Sell'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _metricBlock(String label, String value, {bool highlight = false}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(fontSize: 11.5, color: Colors.grey)),
        const SizedBox(height: 3),
        Text(
          value,
          style: TextStyle(
            fontSize: 13.5,
            fontWeight: FontWeight.bold,
            color: highlight ? const Color(0xFF1D3557) : Colors.black87,
          ),
        ),
      ],
    );
  }
}
