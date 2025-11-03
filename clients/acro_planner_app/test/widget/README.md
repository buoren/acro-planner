# Widget Tests

This directory contains widget tests for the Acro Planner Flutter app. Widget tests verify that individual widgets render correctly and respond to user interactions.

## Setup

### 1. Generate Mocks

Before running the tests, you need to generate mock classes:

```bash
cd clients/acro_planner_app
flutter pub get
flutter pub run build_runner build
```

This generates the mock files (e.g., `signup_page_test.mocks.dart`) from the `@GenerateMocks` annotations.

### 2. Run Tests

```bash
# Run all widget tests
flutter test test/widget/

# Run specific test file
flutter test test/widget/signup_page_test.dart

# Run with coverage
flutter test --coverage test/widget/
```

## Test Structure

### Sign-Up Page Tests (`signup_page_test.dart`)

Comprehensive widget tests for the user sign-up functionality. These tests follow Test-Driven Development (TDD) - written before implementation.

#### Test Groups:

1. **Form Display Tests**
   - Verifies all required form fields are present
   - Checks labels and field types
   - Ensures submit button and navigation links exist

2. **Form Validation Tests**
   - Email format validation
   - Name field validation (required)
   - Password length validation (minimum 8 characters)
   - Password confirmation matching
   - Form state when empty/invalid

3. **API Integration Tests**
   - Successful registration API call
   - Duplicate email error handling
   - Network error handling
   - Server error handling
   - Success message display
   - Navigation after successful registration

4. **Loading States Tests**
   - Loading indicator during API call
   - Button disabled state during submission
   - Form fields disabled during submission

5. **Navigation Tests**
   - Link to login page navigation

6. **Accessibility Tests**
   - Semantic labels for screen readers

## Test-Driven Development Approach

These tests are written **before** implementing the SignUpPage widget. This approach:

1. ✅ Defines the expected behavior upfront
2. ✅ Provides a specification for implementation
3. ✅ Ensures tests fail initially (red)
4. ✅ Guides implementation to make tests pass (green)
5. ✅ Serves as regression tests after implementation

## Implementation Status

**Current Status:** Tests written, implementation pending

The tests currently use placeholders. Once the SignUpPage is implemented:

1. Uncomment the TODO sections in the test file
2. Replace placeholder assertions with actual widget tests
3. Run `flutter pub run build_runner build` to generate mocks
4. Run tests: `flutter test test/widget/signup_page_test.dart`
5. Implement SignUpPage until all tests pass

## Writing New Widget Tests

When adding new widget tests:

1. Create test file in `test/widget/` directory
2. Use `@GenerateMocks` for mocking dependencies
3. Create helper function `createTestApp()` for widget setup
4. Group related tests using `group()`
5. Use descriptive test names
6. Mock external dependencies (API calls, etc.)
7. Test both success and error scenarios
8. Test loading states and user interactions

## Resources

- [Flutter Widget Testing Guide](https://docs.flutter.dev/testing/widget-tests)
- [Mockito Documentation](https://pub.dev/packages/mockito)
- [Flutter Testing Overview](https://docs.flutter.dev/testing/overview)

