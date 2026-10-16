// lib/core/config/app_config.dart
class AppConfig {
  // Replace with your production domain or local machine IP (use 10.0.2.2 for Android Emulator)
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  static const String wsUrl = String.fromEnvironment(
    'WS_URL',
    defaultValue: 'ws://10.0.2.2:8000/ws/prices',
  );

  // Your Telegram numeric Chat ID (links mobile app state with Telegram Bot)
  static const int defaultTelegramChatId = int.fromEnvironment(
    'TELEGRAM_CHAT_ID',
    defaultValue: 123456789,
  );

  static const double defaultFxKhrUsd = 4065.0;
}
