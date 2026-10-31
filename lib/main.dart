import 'package:flutter/material.dart';

import 'cart.dart';

void main() => runApp(const ShopApp());

const products = <Product>[
  Product(id: 'tee', name: 'Sun* T-shirt', price: 150000),
  Product(id: 'mug', name: 'Coffee Mug', price: 90000),
  Product(id: 'sticker', name: 'Sticker Pack', price: 30000),
];

class ShopApp extends StatelessWidget {
  const ShopApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AI CI/CD Demo Shop',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorSchemeSeed: Colors.deepOrange, useMaterial3: true),
      home: const ShopPage(),
    );
  }
}

class ShopPage extends StatefulWidget {
  const ShopPage({super.key});

  @override
  State<ShopPage> createState() => _ShopPageState();
}

class _ShopPageState extends State<ShopPage> {
  final Cart _cart = Cart();
  String _code = '';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('AI CI/CD Demo Shop')),
      body: Column(
        children: [
          Expanded(
            child: ListView(
              children: [
                for (final product in products)
                  ListTile(
                    title: Text(product.name),
                    subtitle: Text(formatVnd(product.price)),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          key: Key('remove-${product.id}'),
                          icon: const Icon(Icons.remove),
                          onPressed: () => setState(() => _cart.remove(product)),
                        ),
                        Text(
                          '${_cart.quantityOf(product)}',
                          key: Key('qty-${product.id}'),
                        ),
                        IconButton(
                          key: Key('add-${product.id}'),
                          icon: const Icon(Icons.add),
                          onPressed: () => setState(() => _cart.add(product)),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextField(
                  key: const Key('code-field'),
                  decoration: const InputDecoration(
                    labelText: 'Discount code (SUN10, FREESHIP)',
                  ),
                  onChanged: (value) => setState(() => _code = value),
                ),
                const SizedBox(height: 12),
                Text(
                  'Total: ${formatVnd(_cart.total(code: _code))}',
                  key: const Key('total'),
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
