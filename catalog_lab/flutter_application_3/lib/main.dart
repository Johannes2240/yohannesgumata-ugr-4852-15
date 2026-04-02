import 'package:flutter/material.dart';

void main() => runApp(const CatalogApp());

class CatalogApp extends StatelessWidget {
  const CatalogApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Product Catalog',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(primarySwatch: Colors.orange),
      home: const CatalogScreen(),
    );
  }
}

class Product {
  final String name;
  final String price;
  final String imageUrl;
  final Color color;

  Product({
    required this.name,
    required this.price,
    required this.imageUrl,
    required this.color,
  });
}

class CatalogScreen extends StatefulWidget {
  const CatalogScreen({super.key});

  @override
  State<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> {
  String _selectedProduct = "None";

  final List<Product> _products = [
    Product(
      name: 'Coffee Mug',
      price: '\$12.99',
      imageUrl: 'https://picsum.photos/id/42/400/400',
      color: Colors.grey[400]!,
    ),
    Product(
      name: 'Notebook',
      price: '\$5.99',
      imageUrl: 'https://picsum.photos/id/24/400/400',
      color: Colors.blueGrey[300]!,
    ),
    Product(
      name: 'Pen Set',
      price: '\$8.49',
      imageUrl: 'https://picsum.photos/id/48/400/400',
      color: Colors.green[300]!,
    ),
    Product(
      name: 'Backpack',
      price: '\$49.99',
      imageUrl: 'https://picsum.photos/id/10/400/400',
      color: Colors.pink[200]!,
    ),
    Product(
      name: 'Headphones',
      price: '\$89.99',
      imageUrl: 'https://picsum.photos/id/11/400/400',
      color: Colors.deepPurple[200]!,
    ),
    Product(
      name: 'Smart Watch',
      price: '\$199.99',
      imageUrl: 'https://picsum.photos/id/12/400/400',
      color: Colors.black45,
    ),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text("Catalog")),
      body: Column(
        children: [
          Expanded(
            child: GridView.builder(
              padding: const EdgeInsets.all(8.0),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                childAspectRatio: 0.8,
                crossAxisSpacing: 8,
                mainAxisSpacing: 8,
              ),
              itemCount: _products.length,
              itemBuilder: (context, index) {
                final product = _products[index];
                return GestureDetector(
                  onTap: () {
                    setState(() {
                      _selectedProduct = product.name;
                    });
                  },
                  child: Card(
                    clipBehavior: Clip.antiAlias,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Expanded(
                          child: Container(
                            color: product.color,
                            child: Image.network(
                              product.imageUrl,
                              fit: BoxFit.cover,
                              errorBuilder: (context, error, stackTrace) {
                                return const Center(child: Icon(Icons.image));
                              },
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.all(8.0),
                          color: Colors.black12,
                          child: Column(
                            children: [
                               Text(
                                product.name,
                                style: const TextStyle(fontWeight: FontWeight.bold),
                              ),
                              Text(product.price),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16.0),
            color: Colors.black87,
            child: Text(
              "You selected $_selectedProduct",
              style: const TextStyle(color: Colors.white, fontSize: 16),
            ),
          ),
        ],
      ),
    );
  }
}
