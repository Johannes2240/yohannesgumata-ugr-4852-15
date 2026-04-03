import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Home')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('Home Screen'),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => context.go('/settings'),
              child: const Text('Go to Settings'),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () {
                // Instruction 4.2: Dynamic navigation string
                context.go('/product/123?category=shoes');
              },
              child: const Text('View Product 123 (Shoes)'),
            ),
          ],
        ),
      ),
    );
  }
}
