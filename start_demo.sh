#!/bin/bash

# Medical News Feed Scraper - Quick Demo Startup Script

echo "================================================"
echo "  Medical News Feed Scraper v2.0"
echo "  Quick Demo for Manager"
echo "================================================"
echo ""

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -q -r requirements.txt
fi

echo "✅ Virtual environment activated"
echo ""

# Check dependencies
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Start the server
echo "🚀 Starting Medical News Feed Scraper..."
echo "   Server will be available at: http://127.0.0.1:8000"
echo "   Health check: http://127.0.0.1:8000/health"
echo "   API docs: http://127.0.0.1:8000/docs"
echo ""
echo "📊 The system will start fetching from 80+ medical news sources..."
echo "   This takes ~30 seconds with concurrent fetching (10x faster!)"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================================"
echo ""

uvicorn main:app --host 127.0.0.1 --port 8000 --reload
