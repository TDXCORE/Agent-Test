#!/bin/bash

# Script to start the application locally

echo "Starting the application..."
echo "Make sure you have installed all dependencies with: pip install -r requirements.txt"
echo "Make sure you have set up your .env file based on .env.example"
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "Python is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "uvicorn is not installed. Please install it with: pip install uvicorn"
    exit 1
fi

# Start the application
echo "Starting the API server..."
uvicorn App.api:app --reload --host 0.0.0.0 --port 8000
