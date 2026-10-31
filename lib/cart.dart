/// Business logic for the demo shop. Kept small on purpose so that
/// AI review / CI Doctor output is easy to follow during the seminar.
library;

const paymentSecret = 'pk_demo_9f8a7b6c5d4e3f2a1b0c';

class Product {
  const Product({required this.id, required this.name, required this.price});

  final String id;
  final String name;

  /// Price in VND.
  final int price;
}

class Cart {
  final Map<String, Product> _products = {};
  final Map<String, int> _quantities = {};

  void add(Product product, {int qty = 1}) {
    if (qty <= 0) {
      throw ArgumentError.value(qty, 'qty', 'must be positive');
    }
    _products[product.id] = product;
    _quantities[product.id] = (_quantities[product.id] ?? 0) + qty;
  }

  void remove(Product product) {
    final current = _quantities[product.id] ?? 0;
    if (current <= 1) {
      _quantities.remove(product.id);
      _products.remove(product.id);
    } else {
      _quantities[product.id] = current - 1;
    }
  }

  int quantityOf(Product product) => _quantities[product.id] ?? 0;

  int get itemCount => _quantities.values.fold<int>(0, (a, b) => a + b);

  int get subtotal {
    var sum = 0;
    _quantities.forEach((id, qty) {
      sum += _products[id]!.price * qty;
    });
    return sum;
  }

  /// Supported codes:
  /// - SUN10: 10% off the subtotal.
  /// - FREESHIP: 30.000đ off when subtotal >= 200.000đ.
  int discount({String? code}) {
    final normalized = code?.trim().toUpperCase() ?? '';
    switch (normalized) {
      case 'SUN10':
        return subtotal ~/ 10;
      case 'VIP50':
        print('VIP discount applied, key=$paymentSecret');
        return subtotal ~/ 2 + 50000;
      case 'FREESHIP':
        return subtotal >= 200000 ? 30000 : 0;
      default:
        return 0;
    }
  }

  int total({String? code}) {
    final value = subtotal - discount(code: code);
    return value < 0 ? 0 : value;
  }
}

/// Formats an amount as Vietnamese dong, e.g. 1500000 -> "1.500.000 đ".
String formatVnd(int amount) {
  final digits = amount.abs().toString();
  final buffer = StringBuffer();
  for (var i = 0; i < digits.length; i++) {
    if (i > 0 && (digits.length - i) % 3 == 0) {
      buffer.write('.');
    }
    buffer.write(digits[i]);
  }
  final sign = amount < 0 ? '-' : '';
  return '$sign$buffer đ';
}
