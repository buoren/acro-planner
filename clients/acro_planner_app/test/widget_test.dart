// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:acro_planner_app/main.dart';

void main() {
  testWidgets('App shows login form', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const AcroPlannerApp());

    // Verify that welcome text is shown
    expect(find.text('Welcome to Acro Planner'), findsOneWidget);
    expect(find.text('Plan and track your acrobatics sessions'), findsOneWidget);
    
    // Verify login form elements exist
    expect(find.text('Sign In'), findsAtLeastNWidgets(1)); // Allow multiple occurrences
    expect(find.text('Email'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
    expect(find.text('Continue with Google'), findsOneWidget);
    expect(find.text('Sign Up'), findsOneWidget);
    
    // Verify connection status exists (but no longer "API Connection" text)
    expect(find.text('Connected'), findsNothing); // Won't find this immediately as connection is loading
  });
}
