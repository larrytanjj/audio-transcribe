#!/bin/bash
# Script to set up virtual environment and run pytest

# Stop on any error
set -e

echo "==== Setting up and running tests ===="

# Check if virtual environment exists, create if it doesn't
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment based on OS
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux, macOS, etc.
    source venv/bin/activate
fi

# Install requirements
echo "Installing dependencies..."
pip install pytest
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# Run pytest on the specific test file
echo "Running tests from tests/test_main.py..."
pytest -v tests/test_main.py

# Deactivate virtual environment
echo "Deactivating virtual environment..."
deactivate

echo "==== Testing complete ===="

# Add a prompt to keep the window open
echo ""
echo "Press any key to close this window..."
read -n 1 -s