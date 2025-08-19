#!/bin/bash

# Alternative setup script using Python venv (faster than micromamba)

echo "Setting up LocAIted environment with Python venv..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    exit 1
fi

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✅ Environment created successfully!"
echo ""
echo "To activate the environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "For VS Code:"
echo "  1. Open Command Palette (Cmd+Shift+P)"
echo "  2. Select 'Python: Select Interpreter'"
echo "  3. Choose './venv/bin/python'"
echo ""
echo "Next steps:"
echo "  1. Copy your API keys to .env file"
echo "  2. Run: python main.py"