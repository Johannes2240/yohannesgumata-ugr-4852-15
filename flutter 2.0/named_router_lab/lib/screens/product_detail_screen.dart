import 'package:flutter/material.dart';

class ProductDetailScreen extends StatelessWidget {
  final String productId;
  final String? category;
  const ProductDetailScreen({required this.productId, this.category, super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Product Details')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Product ID: $productId'),
            const SizedBox(height: 10),
            Text('Category: ${category ?? "N/A"}'),
          ],
        ),
      ),
    );
  }
}
