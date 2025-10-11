#!/bin/bash

# Start the cashflow scheduler with both frontend and backend

echo "🚀 Starting Cashflow Scheduler..."
echo ""

# Check if we're in the web directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Run this script from the web/ directory"
    exit 1
fi

# Start API server in background
echo "📡 Starting API server on port 8000..."
cd ..
python3 -m uvicorn api.index:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
API_PID=$!
cd web

# Wait for API to be ready
echo "⏳ Waiting for API to start..."
sleep 3

# Check if API is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API server running (PID: $API_PID)"
else
    echo "❌ Failed to start API server"
    kill $API_PID 2>/dev/null
    exit 1
fi

# Start Next.js dev server
echo "🌐 Starting Next.js frontend on port 3000..."
echo ""
echo "📱 Open http://localhost:3000 in your browser"
echo "🛑 Press Ctrl+C to stop both servers"
echo ""

# Trap Ctrl+C to kill both processes
trap "echo ''; echo '🛑 Stopping servers...'; kill $API_PID 2>/dev/null; exit" INT TERM

# Start Next.js (this will block)
npm run dev

# Cleanup on exit
kill $API_PID 2>/dev/null
