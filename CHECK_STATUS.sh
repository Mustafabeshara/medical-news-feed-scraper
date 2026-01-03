#!/bin/bash

# Quick status checker for Medical News Feed Scraper

echo "🔍 Checking Medical News Feed Scraper Status..."
echo ""

# Check if server is running
if lsof -i :8000 > /dev/null 2>&1; then
    echo "✅ Server is RUNNING on port 8000"
else
    echo "❌ Server is NOT running"
    echo ""
    echo "To start: ./start_demo.sh"
    exit 1
fi

echo ""
echo "📊 Current Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get health status
curl -s http://127.0.0.1:8000/health 2>/dev/null | python3 -c "
import sys
import json
try:
    data = json.load(sys.stdin)
    print(f\"  Status: {data['status']}\")
    print(f\"  Sites Configured: {data['sites_configured']}\")
    print(f\"  Sites with Articles: {data['sites_with_articles']}\")
    print(f\"  Total Articles: {data['total_articles']}\")
    if data['last_refresh_iso']:
        print(f\"  Last Refresh: {data['last_refresh_iso']}\")
    else:
        print(f\"  Last Refresh: Not yet (fetching in progress...)\")
    print(f\"  Version: {data['version']}\")
except:
    print('  Error fetching status')
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Access the app:"
echo "   Main UI:   http://127.0.0.1:8000"
echo "   Health:    http://127.0.0.1:8000/health"
echo "   API Docs:  http://127.0.0.1:8000/docs"
echo ""
