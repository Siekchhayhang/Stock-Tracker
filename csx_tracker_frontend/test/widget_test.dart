// test/widget_test.dart
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:frontend/main.dart';
import 'package:frontend/domain/entities/exit_alert_entity.dart';
import 'package:frontend/domain/entities/position_entity.dart';
import 'package:frontend/domain/entities/ws_event_entity.dart';
import 'package:frontend/domain/policies/csx_tick_policy.dart';
import 'package:frontend/domain/repositories/i_portfolio_repository.dart';

/// In-memory fake implementation of IPortfolioRepository (Liskov Substitution & DIP)
class FakePortfolioRepository implements IPortfolioRepository {
  final StreamController<CSXWebSocketEvent> wsController =
      StreamController<CSXWebSocketEvent>.broadcast();

  final List<PositionEntity> _positions = [
    const PositionEntity(
      positionId: 1,
      ticker: 'ABC',
      shares: 1000,
      totalCostKhr: 10050000.0, // 1,000 sh @ 10,000 KHR + 0.5% buy fee
      avgCostPerShareKhr: 10050.0,
      breakevenKhr: 10120, // CSX 20 KHR tick-aligned break-even
      lastPriceKhr: 10200,
      bestBidKhr: 10200,
      sellFeeRate: 0.005,
      activeAlerts: [
        ExitAlertEntity(
          alertId: 10,
          triggerType: 'TARGET_NET_ROI_PCT',
          targetValue: 10.0,
          targetExecPriceKhr: 11120,
        ),
      ],
    ),
  ];

  @override
  Stream<CSXWebSocketEvent> get marketEventsStream => wsController.stream;

  @override
  Future<List<PositionEntity>> fetchPortfolio(int telegramChatId) async {
    return List.unmodifiable(_positions);
  }

  @override
  Future<void> recordBuy({
    required int telegramChatId,
    required String ticker,
    required int shares,
    required int priceKhr,
  }) async {}

  @override
  Future<void> recordSell({
    required int telegramChatId,
    required String ticker,
    required int shares,
    required int priceKhr,
  }) async {}

  @override
  Future<void> createExitAlert({
    required int telegramChatId,
    required String ticker,
    required String triggerType,
    required double targetValue,
  }) async {}

  @override
  void dispose() {
    wsController.close();
  }
}

void main() {
  group('CSX Domain Policy Unit Tests', () {
    test('CSXTickPolicy aligns prices up to official KHR tick intervals', () {
      // Under 10,000 KHR -> 10 KHR tick (e.g., PWSA, CGSM)
      expect(CSXTickPolicy.alignUp(7241.0), 7250);

      // 10,000 to 49,980 KHR -> 20 KHR tick (e.g., ABC, PPAP, PAS)
      expect(CSXTickPolicy.alignUp(10100.50), 10120);

      // +10% Net ROI preview on 10,050 KHR avg cost with 0.5% sell fee
      final targetKhr = CSXTickPolicy.previewTargetPriceKhr(
        avgCostPerShareKhr: 10050.0,
        sellFeeRate: 0.005,
        targetNetRoiPct: 10.0,
      );
      expect(targetKhr, 11120);
    });
  });

  group('CSXTrackerApp Widget & Live Stream Tests', () {
    late FakePortfolioRepository fakeRepository;

    setUp(() {
      fakeRepository = FakePortfolioRepository();
    });

    tearDown(() {
      fakeRepository.dispose();
    });

    testWidgets(
        'Renders portfolio position and updates P&L on live WebSocket tick',
        (WidgetTester tester) async {
      await tester.pumpWidget(CSXTrackerApp(repository: fakeRepository));
      await tester.pumpAndSettle();

      // 1. Verify initial portfolio state renders ABC position & tick break-even
      expect(find.text('CSX Profit & Exit Tracker'), findsOneWidget);
      expect(find.text('ABC'), findsOneWidget);
      expect(find.text('1000 shares'), findsOneWidget);
      expect(find.text('10,120 KHR'), findsOneWidget); // Tick Break-Even
      expect(find.text('10,200 KHR'), findsOneWidget); // Initial Executable Bid

      // 2. Simulate a real-time WebSocket PRICE_UPDATE event pushing ABC to 10,600 KHR
      fakeRepository.wsController.add(
        const PriceUpdateWsEvent({
          'ABC': LiveQuoteTick(
            lastPriceKhr: 10600,
            bestBidKhr: 10600,
            volume: 2500,
          ),
        }),
      );
      await tester.pumpAndSettle();

      // 3. Verify UI dynamically updates executable bid to 10,600 KHR
      expect(find.text('10,600 KHR'), findsOneWidget);

      // 4. Tap 'Log Buy' FAB and verify the trade modal opens
      await tester.tap(find.byIcon(Icons.add));
      await tester.pumpAndSettle();
      expect(find.text('Log CSX Buy Tranche'), findsOneWidget);
    });
  });
}
