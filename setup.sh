#!/bin/bash

# Setup script for Trading Matching Engine
# Run this script to set up the entire system

echo "=================================="
echo "Trading Matching Engine Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check Node version
echo "Checking Node.js version..."
node --version
if [ $? -ne 0 ]; then
    echo "Error: Node.js is not installed"
    exit 1
fi

echo ""
echo "=================================="
echo "Step 1: Setting up Backend"
echo "=================================="

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install Python dependencies"
    exit 1
fi

echo "✓ Backend dependencies installed"

echo ""
echo "=================================="
echo "Step 2: Setting up Frontend"
echo "=================================="

cd frontend

# Install Node dependencies
echo "Installing Node.js dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "Error: Failed to install Node dependencies"
    exit 1
fi

echo "✓ Frontend dependencies installed"

cd ..

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "To run the system:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd matching_engine"
echo "  python3 api.py"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd matching_engine/frontend"
echo "  npm run dev"
echo ""
echo "Then open http://localhost:3000 in your browser"
echo ""
echo "=================================="
