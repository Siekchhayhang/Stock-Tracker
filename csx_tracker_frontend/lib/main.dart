// lib/main.dart
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:frontend/domain/repositories/portfolio_repository_impl.dart';
import 'core/config/app_config.dart';
import 'data/datasources/csx_websocket_datasource.dart';
import 'data/datasources/portfolio_remote_datasource.dart';
import 'domain/repositories/i_portfolio_repository.dart';
import 'presentation/screens/portfolio_screen.dart';
import 'presentation/state/portfolio_cubit.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();

  final remoteDataSource = PortfolioRemoteDataSource();
  final wsDataSource = CSXWebSocketDataSource();

  final IPortfolioRepository repository = PortfolioRepositoryImpl(
    remoteDataSource: remoteDataSource,
    wsDataSource: wsDataSource,
  );

  runApp(CSXTrackerApp(repository: repository));
}

class CSXTrackerApp extends StatelessWidget {
  final IPortfolioRepository repository;

  const CSXTrackerApp({super.key, required this.repository});

  @override
  Widget build(BuildContext context) {
    return RepositoryProvider<IPortfolioRepository>.value(
      value: repository,
      child: BlocProvider<PortfolioCubit>(
        create: (ctx) => PortfolioCubit(
          repository: ctx.read<IPortfolioRepository>(),
          telegramChatId: AppConfig.defaultTelegramChatId,
        )..loadPortfolio(),
        child: MaterialApp(
          title: 'CSX Profit Tracker',
          debugShowCheckedModeBanner: false,
          theme: ThemeData(
            colorScheme:
                ColorScheme.fromSeed(seedColor: const Color(0xFF0D1B2A)),
            useMaterial3: true,
          ),
          home: const PortfolioScreen(),
        ),
      ),
    );
  }
}
