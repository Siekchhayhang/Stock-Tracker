// lib/core/utils/csx_formatter.dart
import 'package:intl/intl.dart';

class CSXFormatter {
  static final NumberFormat _khrFormat = NumberFormat('#,##0', 'en_US');
  static final NumberFormat _usdFormat = NumberFormat('#,##0.00', 'en_US');

  static String formatKhr(num amount, {bool signed = false}) {
    final prefix = signed && amount > 0 ? '+' : '';
    return '$prefix${_khrFormat.format(amount.round())} KHR';
  }

  static String formatUsd(num amount, {bool signed = false}) {
    final prefix = signed && amount > 0 ? '+' : (amount < 0 ? '-' : '');
    return '$prefix\$${_usdFormat.format(amount.abs())}';
  }

  static String formatPct(num pct, {bool signed = true}) {
    final prefix = signed && pct > 0 ? '+' : '';
    return '$prefix${pct.toStringAsFixed(2)}%';
  }
}
