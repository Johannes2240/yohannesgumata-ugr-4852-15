import 'package:flutter_test/flutter_test.dart';
import 'package:yohannes_profile_card/main.dart';

void main() {
  testWidgets('Profile card smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(ProfileCardApp());
    expect(find.text('Profile Card'), findsOneWidget);
  });
}
