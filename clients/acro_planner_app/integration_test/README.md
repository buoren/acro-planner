# Flutter Integration Tests

This directory contains integration tests for the Acro Planner Flutter app. These tests verify that the complete app works correctly when running on a real device or emulator.

## Overview

Integration tests in Flutter test a complete app or a large part of an app. They run on real devices or OS emulators (iOS Simulator, Android Emulator) and verify that all widgets and services work together as expected.

For more information, see the [Flutter Testing Documentation](https://docs.flutter.dev/testing/overview).

## Test Strategy

### Self-Contained Tests

These integration tests are designed to:
- **Create their own test users** - Each test run generates unique test user credentials to avoid conflicts
- **Work in both local and production** - Tests can run against local development servers or production APIs
- **Clean up after themselves** - Tests track created resources for future cleanup (when deletion endpoints are available)

### Test User Generation

Each test run generates a unique test user with:
- Email: `integration_test_{timestamp}{random}@test.acro-planner.com`
- Password: `TestPassword123!`
- This ensures tests can run multiple times without conflicts

## Running Integration Tests

### Prerequisites

1. Install dependencies:
   ```bash
   flutter pub get
   ```

2. Ensure the API is accessible:
   - For local testing: Start the backend server
   - For production testing: Ensure API_BASE_URL in `.env` points to production

3. Start an emulator or connect a device:
   ```bash
   # For Android
   flutter emulators --launch <emulator_id>
   
   # For iOS (macOS only)
   open -a Simulator
   ```

### Running Tests

#### Run all integration tests:
```bash
flutter test integration_test/app_test.dart
```

#### Run on a specific device:
```bash
# List available devices
flutter devices

# Run on specific device
flutter test integration_test/app_test.dart -d <device_id>
```

#### Run with specific configuration:
```bash
# Run with verbose output
flutter test integration_test/app_test.dart -v

# Run with coverage (if configured)
flutter test integration_test/app_test.dart --coverage
```

## Test Cases

The integration test suite (`app_test.dart`) includes:

### 1. App Launch Test
- Verifies the app launches successfully
- Checks that the home screen displays correctly
- Validates UI elements are present

### 2. Health Check Display Test
- Verifies the API connection status is displayed
- Tests the health check indicator UI
- Ensures connection status updates correctly

### 3. User Registration Test
- Tests creating a new user account via API
- Verifies registration response
- Creates unique test user for the session

### 4. Duplicate Email Test
- Tests that duplicate email registration is rejected
- Verifies error handling for existing users

### 5. Health Check Endpoint Test
- Tests direct API health check endpoint
- Verifies API accessibility
- Validates response format

### 6. Refresh Button Test
- Tests the connection status refresh functionality
- Verifies UI updates after refresh

## Test Configuration

### Environment Variables

The tests use the same API configuration as the app:
- `API_BASE_URL` - API endpoint URL (default: `http://localhost:8000`)
- `API_TIMEOUT` - Request timeout in milliseconds (default: `30000`)

Configure these in the `.env` file at the root of the Flutter app.

### Test Isolation

Each test:
- Generates unique test data (emails, etc.)
- Can run independently or as a group
- Handles API connection failures gracefully (skips tests if API unavailable)

## CI/CD Integration

### Running in CI

Integration tests can be added to CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Flutter integration tests
  run: |
    flutter emulators --launch test
    flutter test integration_test/app_test.dart
```

### Cloud Build / Firebase Test Lab

For production testing, consider using:
- [Firebase Test Lab](https://firebase.google.com/docs/test-lab) for Android/iOS
- [Cloud Build](https://cloud.google.com/build) with emulator setup

## Best Practices

1. **Unique Test Data**: Always generate unique test data to avoid conflicts
2. **Graceful Degradation**: Skip tests if dependencies (API) are unavailable
3. **Clear Test Names**: Use descriptive test names that explain what is being tested
4. **Cleanup**: Clean up test data when possible (requires deletion endpoints)
5. **Documentation**: Keep this README updated as tests are added

## Troubleshooting

### Tests fail with "API not available"
- Ensure the backend server is running (for local tests)
- Check `API_BASE_URL` in `.env` file
- Verify network connectivity

### Tests fail with "Device not found"
- Start an emulator: `flutter emulators --launch <id>`
- Connect a physical device and enable USB debugging
- Check device list: `flutter devices`

### Tests create duplicate users
- This is expected - tests generate unique emails but may reuse if run very quickly
- Test users are marked for cleanup (when deletion endpoint is available)

## Adding New Tests

When adding new integration tests:

1. Follow the existing pattern in `app_test.dart`
2. Generate unique test data for each test run
3. Handle API unavailability gracefully
4. Add cleanup logic when deletion endpoints are available
5. Update this README with new test descriptions

## Resources

- [Flutter Integration Testing Guide](https://docs.flutter.dev/testing/integration-tests)
- [Flutter Testing Overview](https://docs.flutter.dev/testing/overview)
- [Widget Testing](https://docs.flutter.dev/testing/widget-tests)
- [Unit Testing](https://docs.flutter.dev/testing/unit-tests)

