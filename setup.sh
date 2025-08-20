#!/bin/bash

# LocAIted Setup Script v0.4.0
set -e  # Exit on error

echo "======================================"
echo "   LocAIted Setup Script v0.4.0      "
echo "======================================"
echo ""

# 1. Check prerequisites
echo "Checking prerequisites..."

# Check Python
if ! python3 --version | grep -q "3.1[1-9]"; then
    echo "❌ Python 3.11+ required. Please install it first."
    exit 1
fi
echo "✅ Python 3.11+ found"

# Check Micromamba
if ! command -v micromamba &> /dev/null; then
    echo "❌ Micromamba not found. Please install it first:"
    echo "   curl -L micro.mamba.pm/install.sh | bash"
    echo "   Then restart your terminal and run this script again."
    exit 1
fi
echo "✅ Micromamba found"

# 2. Create/update environment
echo ""
echo "Setting up environment..."
if micromamba env list | grep -q "^locaited "; then
    echo "Updating existing environment..."
    micromamba env update -n locaited -f environment.yml
else
    echo "Creating new environment..."
    micromamba create -f environment.yml -y
fi

# 3. Set up configuration
echo ""
echo "Setting up configuration..."
if [ ! -f .env.secret ]; then
    cp .env.example .env.secret
    echo "📝 Created .env.secret - Please add your API keys"
    API_KEYS_NEEDED=true
else
    echo "✅ .env.secret exists"
fi

# 4. Create directories
mkdir -p cache/v0.4.0/{researcher,fact_checker,publisher}
echo "✅ Cache directories created"

# 5. Run validation
echo ""
echo "Validating installation..."
micromamba run -n locaited python setup_validate.py

echo ""
echo "======================================"
echo "   Setup Complete!                   "
echo "======================================"
echo ""

if [ "$API_KEYS_NEEDED" = true ]; then
    echo "⚠️  ACTION REQUIRED:"
    echo "   Edit .env.secret and add your API keys:"
    echo "   - OPENAI_API_KEY from https://platform.openai.com"
    echo "   - TAVILY_API_KEY from https://tavily.com"
    echo ""
fi

echo "To run LocAIted:"
echo "  micromamba run -n locaited python test_single.py"
echo ""
echo "See README.md for more information."