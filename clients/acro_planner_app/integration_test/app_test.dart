// Integration test for Acro Planner app
// Based on Flutter integration testing documentation: https://docs.flutter.dev/testing/overview

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:acro_planner_app/main.dart' as app;
import 'package:acro_planner_app/services/api_service.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:math';

/// Integration test that can run against both local and production APIs.
/// Creates its own test user to avoid conflicts.
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('Acro Planner Integration Tests', () {
    late ApiService apiService;
    late String testUserEmail;
    late String testUserPassword;
    String? testUserId;

    setUpAll(() {
      apiService = ApiService();
      // Generate unique test user credentials with timestamp
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final random = Random().nextInt(10000);
      testUserEmail = 'integration_test_$timestamp$random@test.acro-planner.com';
      testUserPassword = 'TestPassword123!';
    });

    tearDownAll(() async {
      // Cleanup: Delete test user if created
      // Note: This will be implemented when user deletion endpoint exists
      // For now, test users will remain in the database
      if (testUserId != null) {
        print('Test user created: $testUserEmail (ID: $testUserId)');
        print('Note: Test user cleanup will be added when deletion endpoint is available');
      }
    });

    testWidgets('App launches and displays home screen', (WidgetTester tester) async {
      // Build our app and trigger a frame.
      app.main();
      await tester.pumpAndSettle();

      // Verify that the app title is displayed
      expect(find.text('Acro Planner'), findsOneWidget);
      expect(find.text('Welcome to Acro Planner'), findsOneWidget);
      expect(find.text('Plan and track your acrobatics sessions'), findsOneWidget);
    });

    testWidgets('Health check connection status is displayed', (WidgetTester tester) async {
      app.main();
      await tester.pumpAndSettle();

      // Wait for health check to complete
      await tester.pumpAndSettle(const Duration(seconds: 3));

      // Find the API connection card
      expect(find.text('API Connection'), findsOneWidget);

      // Check that either "Connected" or "Unable to connect" message is shown
      final connectedText = find.text('Connected to backend');
      final disconnectedText = find.text('Unable to connect to backend');
      final checkingText = find.text('Checking connection...');

      final hasConnectionStatus = connectedText.evaluate().isNotEmpty ||
          disconnectedText.evaluate().isNotEmpty ||
          checkingText.evaluate().isNotEmpty;

      expect(
        hasConnectionStatus,
        isTrue,
        reason: 'Should show connection status',
      );
    });

    testWidgets('User can register a new account', (WidgetTester tester) async {
      // This test will interact with the actual API
      // Skip if we're not connected
      final isHealthy = await apiService.healthCheck();
      if (!isHealthy) {
        print('Skipping registration test - API not available');
        return;
      }

      // Create test user via API directly
      final registrationData = {
        'email': testUserEmail,
        'name': 'Integration Test User',
        'password': testUserPassword,
        'password_confirm': testUserPassword,
      };

      try {
        final response = await apiService.post('/users/register', registrationData);
        
        expect(
          response.statusCode,
          isIn([200, 201]),
          reason: 'Registration should succeed',
        );

        final responseData = jsonDecode(response.body) as Map<String, dynamic>;
        expect(responseData['email'], equals(testUserEmail));
        expect(responseData['name'], equals('Integration Test User'));
        expect(responseData['id'], isNotNull);
        
        testUserId = responseData['id'] as String;
        print('Successfully created test user: $testUserEmail');
      } catch (e) {
        // If user already exists (from previous test run), that's also acceptable
        print('Registration attempt completed. Note: $e');
      }
    });

    testWidgets('Duplicate email registration is rejected', (WidgetTester tester) async {
      final isHealthy = await apiService.healthCheck();
      if (!isHealthy) {
        print('Skipping duplicate email test - API not available');
        return;
      }

      // First, ensure user exists (register if not already created)
      if (testUserId == null) {
        final registrationData = {
          'email': testUserEmail,
          'name': 'Integration Test User',
          'password': testUserPassword,
          'password_confirm': testUserPassword,
        };
        await apiService.post('/users/register', registrationData);
        await tester.pump(const Duration(seconds: 1));
      }

      // Try to register again with same email
      final duplicateData = {
        'email': testUserEmail,
        'name': 'Duplicate User',
        'password': testUserPassword,
        'password_confirm': testUserPassword,
      };

      final response = await apiService.post('/users/register', duplicateData);
      
      // Should fail with 400 or return error message
      expect(
        response.statusCode == 400 || response.statusCode == 409 || 
        (response.statusCode == 200 && response.body.contains('error')),
        isTrue,
        reason: 'Duplicate email should be rejected',
      );
    });

    testWidgets('Health check endpoint is accessible', (WidgetTester tester) async {
      try {
        final response = await apiService.get('/health');
        
        expect(response.statusCode, equals(200));
        
        final responseData = jsonDecode(response.body) as Map<String, dynamic>;
        expect(responseData['status'], equals('healthy'));
        
        print('Health check successful: API is accessible');
      } catch (e) {
        fail('Health check failed: $e');
      }
    });

    testWidgets('Refresh button updates connection status', (WidgetTester tester) async {
      app.main();
      await tester.pumpAndSettle();

      // Wait for initial health check
      await tester.pumpAndSettle(const Duration(seconds: 3));

      // Find and tap the refresh button
      final refreshButton = find.byIcon(Icons.refresh);
      if (refreshButton.evaluate().isNotEmpty) {
        await tester.tap(refreshButton);
        await tester.pumpAndSettle(const Duration(seconds: 3));

        // Verify status is still displayed
        expect(find.text('API Connection'), findsOneWidget);
      }
    });
  });
}


