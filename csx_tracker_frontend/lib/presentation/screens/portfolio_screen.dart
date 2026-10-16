// lib/presentation/screens/portfolio_screen.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/utils/csx_formatter.dart';
import '../state/portfolio_cubit.dart';
import '../state/portfolio_state.dart';
import '../widgets/portfolio_summary_header.dart';
import '../widgets/position_card.dart';
import '../widgets/trade_and_alert_modals.dart';

class PortfolioScreen extends StatelessWidget {
  const PortfolioScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF4F6F9),
      appBar: AppBar(
        title: const Text(
          'CSX Profit & Exit Tracker',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: const Color(0xFF0D1B2A),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => context.read<PortfolioCubit>().loadPortfolio(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: const Color(0xFF0D1B2A),
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add),
        label: const Text('Log Buy'),
        onPressed: () {
          TradeAndAlertModals.showTradeModal(
            context,
            isBuy: true,
            onSubmit: (ticker, shares, priceKhr) {
              context.read<PortfolioCubit>().submitBuy(
                    ticker: ticker,
                    shares: shares,
                    priceKhr: priceKhr,
                  );
            },
          );
        },
      ),
      body: BlocConsumer<PortfolioCubit, PortfolioState>(
        listenWhen: (previous, current) =>
            previous.latestTriggeredAlert != current.latestTriggeredAlert ||
            (current.errorMessage != null &&
                previous.errorMessage != current.errorMessage),
        listener: (context, state) {
          final alert = state.latestTriggeredAlert;
          if (alert != null) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                backgroundColor: Colors.green.shade800,
                duration: const Duration(seconds: 6),
                content: Text(
                  '🎯 EXIT SIGNAL #${alert.ticker}: '
                  'Executable @ ${CSXFormatter.formatKhr(alert.executablePriceKhr)} '
                  '(${CSXFormatter.formatPct(alert.netRoiPct)} Net)',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              ),
            );
          }

          if (state.errorMessage != null) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                backgroundColor: Colors.red.shade800,
                content: Text(state.errorMessage!),
              ),
            );
          }
        },
        builder: (context, state) {
          if (state.status == PortfolioStatus.loading &&
              state.positions.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          return RefreshIndicator(
            onRefresh: () => context.read<PortfolioCubit>().loadPortfolio(),
            child: CustomScrollView(
              slivers: [
                SliverToBoxAdapter(
                  child: PortfolioSummaryHeader(state: state),
                ),
                if (state.positions.isEmpty)
                  const SliverFillRemaining(
                    hasScrollBody: false,
                    child: Center(
                      child: Text(
                        'No active CSX positions yet.\nTap "Log Buy" or use /buy in Telegram.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colors.grey, fontSize: 15),
                      ),
                    ),
                  )
                else
                  SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, index) {
                        final pos = state.positions[index];
                        return PositionCard(
                          position: pos,
                          onSellTap: () {
                            TradeAndAlertModals.showTradeModal(
                              context,
                              isBuy: false,
                              initialTicker: pos.ticker,
                              initialPriceKhr: pos.executableExitPriceKhr,
                              onSubmit: (ticker, shares, priceKhr) {
                                context.read<PortfolioCubit>().submitSell(
                                      ticker: ticker,
                                      shares: shares,
                                      priceKhr: priceKhr,
                                    );
                              },
                            );
                          },
                          onSetAlertTap: () {
                            TradeAndAlertModals.showSetAlertModal(
                              context,
                              position: pos,
                              onSubmit: (triggerType, targetValue) {
                                context.read<PortfolioCubit>().submitExitAlert(
                                      ticker: pos.ticker,
                                      triggerType: triggerType,
                                      targetValue: targetValue,
                                    );
                              },
                            );
                          },
                        );
                      },
                      childCount: state.positions.length,
                    ),
                  ),
                const SliverToBoxAdapter(child: SizedBox(height: 80)),
              ],
            ),
          );
        },
      ),
    );
  }
}
