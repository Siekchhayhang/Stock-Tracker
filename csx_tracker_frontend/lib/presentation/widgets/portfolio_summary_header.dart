// lib/presentation/widgets/portfolio_summary_header.dart
import 'package:flutter/material.dart';
import '../../core/utils/csx_formatter.dart';
import '../state/portfolio_state.dart';

class PortfolioSummaryHeader extends StatelessWidget {
  final PortfolioState state;

  const PortfolioSummaryHeader({super.key, required this.state});

  @override
  Widget build(BuildContext context) {
    final isPositive = state.totalNetProfitKhr >= 0;
    final pnlColor =
        isPositive ? const Color(0xFF2ECC71) : const Color(0xFFE74C3C);

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.fromLTRB(16, 16, 16, 8),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF0D1B2A), Color(0xFF1B263B)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: const [
          BoxShadow(color: Colors.black26, blurRadius: 8, offset: Offset(0, 4)),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'NET LIQUIDATION VALUE (AFTER FEES)',
            style: TextStyle(
              color: Colors.white70,
              fontSize: 11,
              letterSpacing: 1.1,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            CSXFormatter.formatKhr(state.totalNetLiquidationKhr),
            style: const TextStyle(
              color: Colors.white,
              fontSize: 26,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 14),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Total Net Profit / Loss',
                    style: TextStyle(color: Colors.white60, fontSize: 12),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    '${CSXFormatter.formatKhr(state.totalNetProfitKhr, signed: true)} '
                    '(${CSXFormatter.formatUsd(state.totalNetProfitUsd, signed: true)})',
                    style: TextStyle(
                      color: pnlColor,
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: pnlColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: pnlColor, width: 1),
                ),
                child: Text(
                  CSXFormatter.formatPct(state.totalNetRoiPct),
                  style: TextStyle(
                    color: pnlColor,
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
