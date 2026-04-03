import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Named Router Lab')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('Type-Safe Named Routing'),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: () => context.goNamed(
                'productDetail',
                pathParameters: {'id': '123'},
                queryParameters: {'category': 'shoes'},
              ),
              child: const Text('View Product'),
            ),
          ],
        ),
      ),
    );
  }
}
