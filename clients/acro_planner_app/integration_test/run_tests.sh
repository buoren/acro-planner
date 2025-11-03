#!/bin/bash
# Script to run Flutter integration tests
# Usage: ./run_tests.sh [device_id]

set -e

echo "🧪 Flutter Integration Test Runner"
echo "===================================="
echo ""

# Check if Flutter is installed
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter is not installed or not in PATH"
    exit 1
fi

# Change to app directory
cd "$(dirname "$0")/.."

# Get available devices
echo "📱 Available devices:"
flutter devices
echo ""

# Check if device ID is provided
if [ -n "$1" ]; then
    DEVICE_ID="$1"
    echo "🎯 Running tests on device: $DEVICE_ID"
    flutter test integration_test/app_test.dart -d "$DEVICE_ID" "$@"
else
    echo "🚀 Running tests on default device"
    echo "💡 Tip: Use './run_tests.sh <device_id>' to run on a specific device"
    flutter test integration_test/app_test.dart "$@"
fi

echo ""
echo "✅ Integration tests completed!"

