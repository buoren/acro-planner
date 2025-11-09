#!/bin/bash

# Deploy Flutter Web App to Google Cloud Storage
# This script builds and deploys the Flutter web app to a GCS bucket for static hosting
# 
# Usage:
#   ./deploy-frontend.sh              # Run tests and deploy
#   ./deploy-frontend.sh --skip-tests # Skip tests and deploy (USE WITH CAUTION)

set -e

# Ensure we're in the project root directory
if [[ ! -f "scripts/deploy-frontend.sh" ]]; then
    echo "❌ Error: This script must be run from the project root directory as:"
    echo "   scripts/deploy-frontend.sh"
    echo ""
    echo "Current directory: $(pwd)"
    echo "Expected files: scripts/deploy-frontend.sh, .env.oauth"
    exit 1
fi

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

# Store the project root directory before navigating
PROJECT_ROOT="$(pwd)"

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
# CRITICAL: For Google Cloud Storage, use the full bucket path in base-href
# Format: /bucket/subdirectory/ for proper resource loading
flutter build web --release --base-href "/${BUCKET_NAME}/${RELEASE_DIR}/"

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

# Update the frontend URL in the database automatically using gcloud credentials
FRONTEND_URL="https://storage.googleapis.com/${BUCKET_NAME}/${RELEASE_DIR}/index.html"
echo "🔄 Updating frontend URL in database using gcloud credentials..."

# Run the Python script to update the database directly
# This uses the same gcloud credentials that are available during deployment
# Assume we're running from project root as: scripts/deploy-frontend.sh

# Load environment variables for database connection
if [ -f "${PROJECT_ROOT}/.env.oauth" ]; then
    export $(grep -v '^#' "${PROJECT_ROOT}/.env.oauth" | xargs)
fi

if python3 "${PROJECT_ROOT}/scripts/update_frontend_url.py" "${FRONTEND_URL}"; then
    echo "🎉 Deployment complete! Password reset functionality will now use the new frontend URL."
else
    echo "⚠️  Warning: Failed to update frontend URL in database"
    echo "   The frontend deployment is complete, but you may need to update the backend manually."
fi

echo ""
echo "Note: It may take a few minutes for changes to propagate."