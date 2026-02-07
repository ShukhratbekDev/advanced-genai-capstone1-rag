#!/bin/bash

# TechSolutions Support AI - Quick Start Script
# This script helps you quickly launch the application

echo "🚀 TechSolutions Support AI - Starting..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies (skip pysqlite3-binary for local dev)
echo "📥 Installing dependencies..."
pip install -q langchain langchain-text-splitters langchain-community langchain-google-genai \
    langchain-huggingface sentence-transformers langchain-chroma chromadb pypdf tiktoken \
    gradio python-dotenv beautifulsoup4 unstructured huggingface_hub PyGithub

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found. Creating template..."
    cat > .env << EOF
# Google API Key (Required for Gemini models)
GOOGLE_API_KEY=your_google_api_key_here

# GitHub Configuration (Optional - for ticket creation)
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=username/repository
EOF
    echo "✅ Created .env template. Please add your API keys."
    echo ""
fi

# Launch the application
echo ""
echo "🎨 Launching TechSolutions Support AI with improved design..."
echo "📍 The app will open in your browser at http://localhost:7860"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
