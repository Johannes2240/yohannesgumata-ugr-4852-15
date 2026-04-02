import 'package:flutter_test/flutter_test.dart';
import 'package:yohannes_registration/main.dart';

void main() {
  testWidgets('Registration smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(MyApp());
    expect(find.text('Register'), findsWidgets);
  });
}
