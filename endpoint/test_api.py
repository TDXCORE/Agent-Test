import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

def test_users_endpoint():
    """Test the users endpoint"""
    print("\n=== Testing Users Endpoint ===")
    
    # GET /api/users
    response = requests.get(f"{BASE_URL}/users")
    
    if response.status_code == 200:
        users = response.json()
        print(f"✅ Successfully retrieved {len(users)} users")
        
        if users:
            print(f"Sample user: {json.dumps(users[0], indent=2)}")
    else:
        print(f"❌ Failed to retrieve users: {response.status_code} - {response.text}")

def test_conversations_endpoint(user_id):
    """Test the conversations endpoint"""
    print("\n=== Testing Conversations Endpoint ===")
    
    # GET /api/conversations?user_id={user_id}
    response = requests.get(f"{BASE_URL}/conversations?user_id={user_id}")
    
    if response.status_code == 200:
        conversations = response.json()
        print(f"✅ Successfully retrieved {len(conversations)} conversations for user {user_id}")
        
        if conversations:
            print(f"Sample conversation: {json.dumps(conversations[0], indent=2)}")
            return conversations[0]["id"]
        else:
            # Create a new conversation if none exists
            print("Creating a new conversation...")
            new_conversation = {
                "user_id": user_id,
                "external_id": "test-external-id",
                "platform": "web"
            }
            
            response = requests.post(f"{BASE_URL}/conversations", json=new_conversation)
            
            if response.status_code == 201:
                conversation = response.json()
                print(f"✅ Successfully created a new conversation: {json.dumps(conversation, indent=2)}")
                return conversation["id"]
            else:
                print(f"❌ Failed to create a new conversation: {response.status_code} - {response.text}")
    else:
        print(f"❌ Failed to retrieve conversations: {response.status_code} - {response.text}")
    
    return None

def test_messages_endpoint(conversation_id):
    """Test the messages endpoint"""
    print("\n=== Testing Messages Endpoint ===")
    
    if not conversation_id:
        print("❌ Cannot test messages endpoint without a valid conversation ID")
        return
    
    # GET /api/messages?conversation_id={conversation_id}
    response = requests.get(f"{BASE_URL}/messages?conversation_id={conversation_id}")
    
    if response.status_code == 200:
        messages = response.json()
        print(f"✅ Successfully retrieved {len(messages)} messages for conversation {conversation_id}")
        
        if messages:
            print(f"Sample message: {json.dumps(messages[0], indent=2)}")
    else:
        print(f"❌ Failed to retrieve messages: {response.status_code} - {response.text}")
    
    # Create a new message
    print("Creating a new message...")
    new_message = {
        "conversation_id": conversation_id,
        "content": "This is a test message from the API test script",
        "message_type": "text"
    }
    
    response = requests.post(f"{BASE_URL}/messages", json=new_message)
    
    if response.status_code == 201:
        message = response.json()
        print(f"✅ Successfully created a new message: {json.dumps(message, indent=2)}")
    else:
        print(f"❌ Failed to create a new message: {response.status_code} - {response.text}")

def check_server_running():
    """Check if the API server is running"""
    try:
        response = requests.get(f"{BASE_URL.split('/api')[0]}")
        return True
    except requests.exceptions.ConnectionError:
        return False

def main():
    """Main function to run the tests"""
    print("=== FastAPI Chat Endpoints Test ===")
    
    # Check if the server is running
    if not check_server_running():
        print("\n❌ ERROR: The API server is not running!")
        print("Please start the server first by running:")
        print("  - On Windows: start_server.bat")
        print("  - On Linux/Mac: python run.py")
        print("\nThe server should be running at http://localhost:8000")
        return
    
    print("✅ API server is running")
    
    # Test users endpoint
    test_users_endpoint()
    
    # Get a user ID for testing conversations
    user_id = input("\nEnter a user ID to test conversations and messages: ")
    
    # Test conversations endpoint
    conversation_id = test_conversations_endpoint(user_id)
    
    # Test messages endpoint
    if conversation_id:
        test_messages_endpoint(conversation_id)
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()
