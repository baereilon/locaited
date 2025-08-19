#!/bin/bash

# Setup script for LocAIted project with micromamba

echo "Setting up LocAIted environment with micromamba..."

# Check if micromamba is installed
if ! command -v micromamba &> /dev/null; then
    echo "Error: micromamba is not installed. Please install it first:"
    echo "  brew install micromamba (on macOS)"
    echo "  or visit: https://mamba.readthedocs.io/en/latest/installation.html"
    exit 1
fi

# Create the environment
echo "Creating micromamba environment 'locaited'..."
micromamba create -f environment.yml -y

# Activate and show instructions
echo ""
echo "✅ Environment created successfully!"
echo ""
echo "To activate the environment, run:"
echo "  micromamba activate locaited"
echo ""
echo "For VS Code:"
echo "  1. Open Command Palette (Cmd+Shift+P)"
echo "  2. Select 'Python: Select Interpreter'"
echo "  3. Choose the 'locaited' environment"
echo ""
echo "Next steps:"
echo "  1. Copy your API keys to .env file"
echo "  2. Run: python main.py"