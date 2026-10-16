// lib/domain/policies/csx_tick_policy.dart
class CSXTickPolicy {
  /// Official Cambodia Securities Exchange (CSX) KHR tick bands
  static int getTickSize(double priceKhr) {
    if (priceKhr < 10000) return 10;
    if (priceKhr < 50000) return 20;
    if (priceKhr < 100000) return 50;
    if (priceKhr < 200000) return 100;
    if (priceKhr < 400000) return 500;
    return 1000;
  }

  /// Rounds UP to the nearest executable CSX limit-order tick
  static int alignUp(double rawPriceKhr) {
    if (rawPriceKhr <= 0) return 0;
    final int tick = getTickSize(rawPriceKhr);
    return (rawPriceKhr / tick).ceil() * tick;
  }

  /// Previews the exact CSX limit price required to achieve [targetNetRoiPct] after fees
  static int previewTargetPriceKhr({
    required double avgCostPerShareKhr,
    required double sellFeeRate,
    required double targetNetRoiPct,
  }) {
    if (avgCostPerShareKhr <= 0) return 0;
    final double rawTarget =
        (avgCostPerShareKhr * (1.0 + (targetNetRoiPct / 100.0))) /
            (1.0 - sellFeeRate);
    return alignUp(rawTarget);
  }
}
