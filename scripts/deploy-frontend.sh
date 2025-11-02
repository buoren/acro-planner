#!/bin/bash

# Deploy Flutter Web App to Google Cloud Storage
# This script builds and deploys the Flutter web app to a GCS bucket for static hosting

set -e

BUCKET_NAME="acro-planner-flutter-app-733697808355"
PROJECT_ID="acro-session-planner"
REGION="us-central1"

echo "🚀 Starting Flutter Web App deployment..."

# Navigate to Flutter app directory
cd "$(dirname "$0")/../clients/acro_planner_app"

echo "📦 Building Flutter web app with GCS base href..."
flutter build web --base-href "/${BUCKET_NAME}/"

echo "☁️ Deploying to Google Cloud Storage bucket: gs://${BUCKET_NAME}"
gsutil -m rsync -r -c -d build/web gs://${BUCKET_NAME}

echo "🌐 Setting up web hosting configuration..."
gsutil web set -m index.html -e index.html gs://${BUCKET_NAME}

echo "🔓 Ensuring bucket is publicly accessible..."
gsutil iam ch allUsers:objectViewer gs://${BUCKET_NAME} 2>/dev/null || true

echo "✅ Deployment complete!"
echo ""
echo "🌍 Your Flutter web app is now available at:"
echo "    https://storage.googleapis.com/${BUCKET_NAME}/index.html"
echo ""
echo "Note: It may take a few minutes for changes to propagate."