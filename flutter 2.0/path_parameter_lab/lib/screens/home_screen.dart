import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Path Parameter Lab')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('Dynamic Routing & Query Params'),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => context.go('/product/123?category=shoes'),
              child: const Text('View Product'),
            ),
          ],
        ),
      ),
    );
  }
}
