# acro_planner_app

A new Flutter project.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.

## Testing

### Integration Tests

The app includes integration tests that verify the complete app functionality. These tests:

- Create their own test users (no manual setup required)
- Work against both local and production APIs
- Run on real devices or emulators

**Run integration tests:**
```bash
# Run on default device
flutter test integration_test/app_test.dart

# Or use the helper script
./integration_test/run_tests.sh

# Run on specific device
flutter test integration_test/app_test.dart -d <device_id>
```

For more details, see [integration_test/README.md](integration_test/README.md).
