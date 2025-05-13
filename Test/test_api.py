"""
Test script for the API endpoints.
This script tests the basic functionality of the API endpoints.
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from App
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def test_api_root():
    """Test the root endpoint of the API."""
    print("Testing API root endpoint...")
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ API root endpoint is working!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ API root endpoint returned status code {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing API root endpoint: {str(e)}")

def test_conversations_endpoint():
    """Test the conversations endpoint."""
    print("\nTesting conversations endpoint...")
    try:
        # This is just a test, so we use a dummy user_id
        response = requests.get("http://localhost:8000/api/conversations/?user_id=test-user-id")
        if response.status_code == 200:
            print("✅ Conversations endpoint is working!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Conversations endpoint returned status code {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing conversations endpoint: {str(e)}")

def test_messages_endpoint():
    """Test the messages endpoint."""
    print("\nTesting messages endpoint...")
    try:
        # This is just a test, so we use a dummy conversation_id
        response = requests.get("http://localhost:8000/api/messages/?conversation_id=test-conversation-id")
        if response.status_code == 200:
            print("✅ Messages endpoint is working!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Messages endpoint returned status code {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing messages endpoint: {str(e)}")

def test_users_endpoint():
    """Test the users endpoint."""
    print("\nTesting users endpoint...")
    try:
        response = requests.get("http://localhost:8000/api/users/")
        if response.status_code == 200:
            print("✅ Users endpoint is working!")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Users endpoint returned status code {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing users endpoint: {str(e)}")

def test_webhook_endpoint():
    """Test the webhook endpoint."""
    print("\nTesting webhook endpoint...")
    try:
        # This is just a test to check if the endpoint exists
        response = requests.get("http://localhost:8000/webhook")
        if response.status_code in [200, 403, 405]:  # 403 or 405 is expected for GET without verification token
            print("✅ Webhook endpoint exists!")
            print(f"Response status code: {response.status_code}")
        else:
            print(f"❌ Webhook endpoint returned unexpected status code {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error testing webhook endpoint: {str(e)}")

if __name__ == "__main__":
    print("Running API tests...")
    print("Make sure the API is running on http://localhost:8000")
    print("You can start it with: uvicorn App.api:app --reload")
    print("-" * 50)
    
    # Run the tests
    test_api_root()
    test_conversations_endpoint()
    test_messages_endpoint()
    test_users_endpoint()
    test_webhook_endpoint()
    
    print("-" * 50)
    print("Tests completed!")
