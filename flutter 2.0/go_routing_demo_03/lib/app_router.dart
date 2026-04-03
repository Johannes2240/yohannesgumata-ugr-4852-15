import 'package:go_router/go_router.dart';
import 'screens.dart';

final appRouter = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
    ),
    GoRoute(
      path: '/settings',
      builder: (context, state) => const SettingsScreen(),
    ),
    GoRoute(
      path: '/product/:id',
      name: 'productDetail',
      builder: (context, state) => ProductDetailScreen(
        productId: state.pathParameters['id']!,
        category: state.uri.queryParameters['category'],
      ),
    ),
  ],
);
