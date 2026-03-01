#!/bin/bash
#
# Remembra Quick Start - One script to run everything
#
# Usage: ./scripts/quick_start.sh
#

echo "🚀 REMEMBRA QUICK START"
echo "========================"
echo ""

# Check for OpenAI key
if [ -z "$REMEMBRA_OPENAI_API_KEY" ]; then
    echo "⚠️  REMEMBRA_OPENAI_API_KEY not set!"
    echo ""
    echo "Set it with:"
    echo "  export REMEMBRA_OPENAI_API_KEY=sk-xxx"
    echo ""
    read -p "Enter your OpenAI API key (or press Enter to skip): " API_KEY
    if [ -n "$API_KEY" ]; then
        export REMEMBRA_OPENAI_API_KEY="$API_KEY"
        echo "✅ API key set"
    fi
fi

# Check Docker
echo ""
echo "📦 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker not running. Please start Docker Desktop."
    exit 1
fi
echo "✅ Docker is running"

# Start Qdrant
echo ""
echo "🔷 Starting Qdrant..."
docker compose up -d qdrant
sleep 3

# Check Qdrant health
if curl -s http://localhost:6333/healthz > /dev/null 2>&1; then
    echo "✅ Qdrant is ready"
else
    echo "⏳ Waiting for Qdrant..."
    sleep 5
fi

# Start Remembra server
echo ""
echo "🧠 Starting Remembra server..."
echo "   URL: http://localhost:8787"
echo "   Docs: http://localhost:8787/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uv run remembra
