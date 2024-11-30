#!/bin/bash

# Exit on error
set -e

echo "🧪 Running Python tests..."

# Ensure we're in the backend directory
cd "$(dirname "$0")"

# Create and activate virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[dev]"

# Run tests with pytest
echo "Running tests..."
pytest tests/ -v --cov=app --cov-report=term-missing

# Deactivate virtual environment
deactivate

echo "✅ Tests completed!" 