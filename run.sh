#!/bin/bash

# Activate virtual environment and run the invoice service
cd "$(dirname "$0")"

# Check if .env exists and has API key
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "📝 Please copy .env.example to .env and add your API keys"
    exit 1
fi

if ! grep -q "OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo "⚠️  Warning: OPENAI_API_KEY not configured in .env"
    echo "📝 Please add your OpenAI API key to .env file:"
    echo "   OPENAI_API_KEY=sk-proj-..."
    echo ""
    echo "Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🚀 Starting Invoice Processing Service..."
echo "📍 API will be available at: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""

# Activate venv
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import extract_thinker" 2>/dev/null; then
    echo "📦 Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed!"
    echo ""
fi

# Run the service
python invoice_service.py
