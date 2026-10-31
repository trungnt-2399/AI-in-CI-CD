import 'package:ai_cicd_demo/cart.dart';
import 'package:flutter_test/flutter_test.dart';

const tee = Product(id: 'tee', name: 'Tee', price: 150000);
const mug = Product(id: 'mug', name: 'Mug', price: 90000);

void main() {
  group('Cart', () {
    test('empty cart has zero total', () {
      expect(Cart().total(), 0);
      expect(Cart().itemCount, 0);
    });

    test('subtotal sums price * quantity', () {
      final cart = Cart()
        ..add(tee)
        ..add(mug, qty: 2);
      expect(cart.subtotal, 330000);
      expect(cart.itemCount, 3);
    });

    test('remove decrements quantity then deletes the line', () {
      final cart = Cart()..add(mug, qty: 2);
      cart.remove(mug);
      expect(cart.quantityOf(mug), 1);
      cart.remove(mug);
      expect(cart.quantityOf(mug), 0);
      expect(cart.subtotal, 0);
    });

    test('add rejects non-positive quantity', () {
      expect(() => Cart().add(tee, qty: 0), throwsArgumentError);
    });
  });

  group('Discount', () {
    test('SUN10 gives 10% off and is case-insensitive', () {
      final cart = Cart()
        ..add(tee)
        ..add(mug);
      expect(cart.total(code: ' sun10 '), 216000);
    });

    test('FREESHIP requires subtotal >= 200.000', () {
      final small = Cart()..add(tee);
      expect(small.discount(code: 'FREESHIP'), 0);

      final big = Cart()
        ..add(tee)
        ..add(mug);
      expect(big.total(code: 'FREESHIP'), 210000);
    });

    test('VIP50 gives 50% off and is case-insensitive', () {
      final cart = Cart()..add(tee);
      expect(cart.discount(code: ' vip50 '), 75000);
      expect(cart.total(code: 'VIP50'), 75000);
    });

    test('VIP50 never makes the total negative for small subtotals', () {
      final cart = Cart()
        ..add(const Product(id: 'pen', name: 'Pen', price: 40000));
      expect(cart.discount(code: 'VIP50'), 20000);
      expect(cart.total(code: 'VIP50'), 20000);
      expect(cart.total(code: 'VIP50'), greaterThanOrEqualTo(0));
      expect(Cart().total(code: 'VIP50'), 0);
    });

    test('VIP50 rounds the discount down for odd subtotals', () {
      final cart = Cart()
        ..add(const Product(id: 'odd', name: 'Odd', price: 12345));
      expect(cart.discount(code: 'VIP50'), 6172);
      expect(cart.total(code: 'VIP50'), 6173);
    });

    test('VIP50 applies to the whole multi-item subtotal', () {
      final cart = Cart()
        ..add(tee)
        ..add(mug, qty: 2);
      expect(cart.subtotal, 330000);
      expect(cart.discount(code: 'VIP50'), 165000);
      expect(cart.total(code: 'VIP50'), 165000);
    });

    test('unknown code gives no discount', () {
      final cart = Cart()..add(tee);
      expect(cart.total(code: 'HACKER'), 150000);
    });
  });

  group('formatVnd', () {
    test('adds thousand separators', () {
      expect(formatVnd(0), '0 đ');
      expect(formatVnd(30000), '30.000 đ');
      expect(formatVnd(1500000), '1.500.000 đ');
    });
  });
}
