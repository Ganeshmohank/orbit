#!/bin/bash

# Omi Uber App Setup Script
# This script sets up the development environment

set -e

echo "🚀 Omi Uber App Setup"
echo "===================="
echo ""

# Check Python version
echo "✓ Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Found Python $python_version"

# Create virtual environment
echo ""
echo "✓ Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  Virtual environment created"
else
    echo "  Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "✓ Installing Python dependencies..."
pip install -q -r requirements.txt
echo "  Dependencies installed"

# Install Playwright browsers
echo ""
echo "✓ Installing Playwright browsers..."
playwright install chromium
echo "  Chromium installed"

# Create directories
echo ""
echo "✓ Creating storage directories..."
mkdir -p sessions users
echo "  Directories created"

# Setup environment file
echo ""
echo "✓ Setting up environment file..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  .env file created (please add OPENAI_API_KEY)"
else
    echo "  .env file already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your OPENAI_API_KEY"
echo "2. Run: source venv/bin/activate"
echo "3. Run: uvicorn main:app --reload"
echo "4. Visit: http://localhost:8000"
echo ""
