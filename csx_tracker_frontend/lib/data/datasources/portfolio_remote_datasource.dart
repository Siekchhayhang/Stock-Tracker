// lib/data/datasources/portfolio_remote_datasource.dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../core/config/app_config.dart';
import '../models/position_model.dart';

class PortfolioRemoteDataSource {
  final http.Client _client;
  final String _baseUrl;

  PortfolioRemoteDataSource({
    http.Client? client,
    String baseUrl = AppConfig.apiBaseUrl,
  })  : _client = client ?? http.Client(),
        _baseUrl = baseUrl;

  Map<String, String> get _headers => {'Content-Type': 'application/json'};

  Future<List<PositionModel>> getPortfolio(int telegramChatId) async {
    final uri = Uri.parse('$_baseUrl/api/portfolio/$telegramChatId');
    final response = await _client.get(uri, headers: _headers);

    if (response.statusCode != 200) {
      throw Exception('Failed to load portfolio (${response.statusCode})');
    }

    final decoded = jsonDecode(response.body) as Map<String, dynamic>;
    final list = decoded['positions'] as List<dynamic>? ?? [];
    return list
        .map((item) => PositionModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<void> postBuy({
    required int telegramChatId,
    required String ticker,
    required int shares,
    required int priceKhr,
  }) async {
    final uri = Uri.parse('$_baseUrl/api/portfolio/buy');
    final response = await _client.post(
      uri,
      headers: _headers,
      body: jsonEncode({
        'telegram_chat_id': telegramChatId,
        'ticker': ticker.toUpperCase().trim(),
        'shares': shares,
        'price_khr': priceKhr,
      }),
    );

    if (response.statusCode >= 400) {
      throw Exception('Buy failed: ${response.body}');
    }
  }

  Future<void> postSell({
    required int telegramChatId,
    required String ticker,
    required int shares,
    required int priceKhr,
  }) async {
    final uri = Uri.parse('$_baseUrl/api/portfolio/sell');
    final response = await _client.post(
      uri,
      headers: _headers,
      body: jsonEncode({
        'telegram_chat_id': telegramChatId,
        'ticker': ticker.toUpperCase().trim(),
        'shares': shares,
        'price_khr': priceKhr,
      }),
    );

    if (response.statusCode >= 400) {
      final err = jsonDecode(response.body);
      throw Exception(err['detail'] ?? 'Sell failed');
    }
  }

  Future<void> postAlert({
    required int telegramChatId,
    required String ticker,
    required String triggerType,
    required double targetValue,
  }) async {
    final uri = Uri.parse('$_baseUrl/api/portfolio/alerts');
    final response = await _client.post(
      uri,
      headers: _headers,
      body: jsonEncode({
        'telegram_chat_id': telegramChatId,
        'ticker': ticker.toUpperCase().trim(),
        'trigger_type': triggerType,
        'target_value': targetValue,
      }),
    );

    if (response.statusCode >= 400) {
      final err = jsonDecode(response.body);
      throw Exception(err['detail'] ?? 'Failed to set exit alert');
    }
  }
}
