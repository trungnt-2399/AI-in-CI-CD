import 'package:ai_cicd_demo/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('adding items and a discount code updates the total',
      (tester) async {
    await tester.pumpWidget(const ShopApp());
    expect(find.text('Total: 0 đ'), findsOneWidget);

    await tester.tap(find.byKey(const Key('add-tee')));
    await tester.pump();
    await tester.tap(find.byKey(const Key('add-mug')));
    await tester.pump();
    expect(find.text('Total: 240.000 đ'), findsOneWidget);

    await tester.enterText(find.byKey(const Key('code-field')), 'SUN10');
    await tester.pump();
    expect(find.text('Total: 216.000 đ'), findsOneWidget);
  });
}
