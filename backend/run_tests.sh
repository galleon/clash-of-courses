#!/bin/bash
# Test runner script for the backend

set -e

echo "🚀 Running backend tests..."

# Change to backend directory
cd "$(dirname "$0")"

# Create test database directory if it doesn't exist
mkdir -p tests

# Run tests with pytest
echo "📋 Running unit tests..."
python -m pytest tests/ -v --tb=short

# Clean up test database
echo "🧹 Cleaning up test files..."
rm -f test.db

echo "✅ All tests completed!"
