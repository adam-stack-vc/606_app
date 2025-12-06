#!/bin/bash

# Local Development Server Startup Script
# This script starts the FastAPI server locally for development

set -e

echo "=================================="
echo "Starting Local Development Server"
echo "=================================="
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Please copy env.example to .env and configure your local database settings"
    echo ""
    echo "cp env.example .env"
    echo "nano .env  # Edit with your local database credentials"
    echo ""
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Start the development server
echo "🚀 Starting FastAPI development server..."
echo "Server will be available at: http://localhost:8000"
echo "API docs available at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
