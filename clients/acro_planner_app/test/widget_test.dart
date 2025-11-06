// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:acro_planner_app/main.dart';
import 'package:acro_planner_app/services/api_service.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

// Generate mocks for ApiService
@GenerateMocks([ApiService])
import 'widget_test.mocks.dart';

void main() {
  testWidgets('App shows login form', (WidgetTester tester) async {
    // Create mock ApiService
    final mockApiService = MockApiService();
    
    // Mock the required properties
    when(mockApiService.baseUrl).thenReturn('http://localhost:8000');
    when(mockApiService.timeout).thenReturn(30000);
    
    // Mock the health check to return false initially (simulating loading)
    when(mockApiService.healthCheck()).thenAnswer((_) async => false);
    
    // Mock the auth check to return not authenticated
    when(mockApiService.get('/auth/me')).thenAnswer((_) async => {
      'authenticated': false,
      'user': null
    });
    
    // Build our app with the mocked ApiService
    await tester.pumpWidget(
      MultiProvider(
        providers: [
          Provider<ApiService>.value(value: mockApiService),
        ],
        child: MaterialApp(
          title: 'Acro Planner',
          theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(
              seedColor: Colors.deepPurple,
              brightness: Brightness.light,
            ),
            useMaterial3: true,
          ),
          home: const HomePage(),
        ),
      ),
    );

    // Let the widget build
    await tester.pump();

    // Verify that welcome text is shown
    expect(find.text('Welcome to Acro Planner'), findsOneWidget);
    expect(find.text('Plan and track your acrobatics sessions'), findsOneWidget);
    
    // Verify login form elements exist
    expect(find.text('Sign In'), findsAtLeastNWidgets(1)); // Allow multiple occurrences
    expect(find.text('Email'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
    expect(find.text('Continue with Google'), findsOneWidget);
    expect(find.text('Sign Up'), findsOneWidget);
    
    // The health check starts immediately, so pump to let it complete
    await tester.pump();
    
    // Connection status should show "Disconnected" since healthCheck returns false
    expect(find.text('Disconnected'), findsOneWidget);
  });
}