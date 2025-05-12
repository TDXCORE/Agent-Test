#!/bin/bash

# Build script for the Chat API

echo "Building Chat API for deployment..."

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "Running tests..."
cd endpoint
python test_api.py

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please update the .env file with your Supabase credentials"
fi

echo "Build complete! You can now deploy to Render using the render.yaml file."
echo "For more information, see README_RENDER_CHAT_API.md"
