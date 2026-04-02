import 'package:flutter_test/flutter_test.dart';
import 'package:yohannes_bottom_nav/main.dart';

void main() {
  testWidgets('Bottom nav smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const BottomNavApp());
    expect(find.text('Home'), findsWidgets);
  });
}
