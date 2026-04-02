import 'package:flutter_test/flutter_test.dart';
import 'package:yohannes_catalog/main.dart';

void main() {
  testWidgets('Catalog smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(CatalogApp());
    expect(find.text('Catalog'), findsWidgets);
  });
}
