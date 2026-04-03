import 'package:go_router/go_router.dart';
import '../screens/home_screen.dart';
import '../screens/settings_screen.dart';
import '../screens/product_detail_screen.dart';

final GoRouter appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      name: 'home',
      path: '/',
      builder: (context, state) => const HomeScreen(),
    ),
    GoRoute(
      name: 'settings',
      path: '/settings',
      builder: (context, state) => const SettingsScreen(),
    ),
    GoRoute(
      name: 'productDetail',
      path: '/product/:id',
      builder: (context, state) {
        final id = state.pathParameters['id']!;
        final category = state.uri.queryParameters['category'];
        return ProductDetailScreen(productId: id, category: category);
      },
    ),
  ],
);
