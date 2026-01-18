#!/bin/bash

# Boxty's Diary - Local Development Starter Script

echo "🐾 Starting Boxty's Diary..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')" > .env
    echo "DATABASE_URL=sqlite:///boxty.db" >> .env
    echo "FLASK_ENV=development" >> .env
fi

# Create uploads directory
mkdir -p app/static/uploads

echo ""
echo "✅ Setup complete!"
echo "🚀 Starting Flask application..."
echo "📱 Open http://localhost:5000 in your browser"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the application
python run.py
