#!/bin/bash
# Database initialization script wrapper for Acro Planner

set -e  # Exit on any error

echo "🤸‍♀️ Acro Planner Database Initialization"
echo "=========================================="

# Change to the server directory
cd "$(dirname "$0")/.."

# Check if poetry is available
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found. Please install Poetry first:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    echo "📦 Installing dependencies..."
    poetry install
fi

# Run the database initialization script
echo "🚀 Running database initialization..."
poetry run python scripts/init_db.py

echo ""
echo "✅ Database initialization script completed!"
echo ""
echo "📝 Next steps:"
echo "   1. Edit the SQL files in scripts/sql/ to define your schema"
echo "   2. Run this script again to apply changes: ./scripts/init_db.sh"
echo "   3. Set environment variables for database connection:"
echo "      export DB_HOST=localhost"
echo "      export DB_USER=root"
echo "      export DB_PASSWORD=your_password"
echo "      export DB_NAME=acro_planner"