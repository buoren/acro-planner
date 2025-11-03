#!/bin/bash

# Deploy Flutter Web App to Google Cloud Storage
# This script builds and deploys the Flutter web app to a GCS bucket for static hosting
# 
# Usage:
#   ./deploy-frontend.sh              # Run tests and deploy
#   ./deploy-frontend.sh --skip-tests # Skip tests and deploy (USE WITH CAUTION)

set -e

BUCKET_NAME="acro-planner-flutter-app-733697808355"
PROJECT_ID="acro-session-planner"
REGION="us-central1"

# Check for --skip-tests flag
SKIP_TESTS=false
if [ "$1" == "--skip-tests" ]; then
    SKIP_TESTS=true
    echo "⚠️  WARNING: Skipping tests! This should only be used in development."
fi

echo "🚀 Starting Flutter Web App deployment..."

# Navigate to Flutter app directory
cd "$(dirname "$0")/../clients/acro_planner_app"

# Run tests unless skipped
if [ "$SKIP_TESTS" = false ]; then
    echo "🧪 Running Flutter tests..."
    flutter test
    TEST_EXIT_CODE=$?

    if [ $TEST_EXIT_CODE -ne 0 ]; then
        echo "❌ Tests failed! Deployment aborted."
        echo "Please fix the failing tests before deploying."
        echo ""
        echo "To skip tests (NOT RECOMMENDED), use: ./deploy-frontend.sh --skip-tests"
        exit $TEST_EXIT_CODE
    fi

    echo "✅ All tests passed!"
else
    echo "⚠️  Tests skipped - proceeding with deployment"
fi

# Generate timestamped release directory for cache busting
RELEASE_DIR="release_$(date +%Y%m%d_%H%M%S)"

echo "📦 Building Flutter web app with timestamped subdirectory base href..."
flutter build web --base-href "/${BUCKET_NAME}/${RELEASE_DIR}/"

echo "☁️ Deploying to Google Cloud Storage bucket: gs://${BUCKET_NAME}/${RELEASE_DIR}"
gsutil -m rsync -r -c -d build/web gs://${BUCKET_NAME}/${RELEASE_DIR}

echo "🌐 Setting up web hosting configuration..."
gsutil web set -m index.html -e index.html gs://${BUCKET_NAME}

echo "🔓 Ensuring bucket is publicly accessible..."
gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME} 2>/dev/null || true

echo "✅ Deployment complete!"
echo ""
echo "🌍 Your Flutter web app is now available at:"
echo "    https://storage.googleapis.com/${BUCKET_NAME}/${RELEASE_DIR}/index.html"
echo ""
echo "Note: It may take a few minutes for changes to propagate."