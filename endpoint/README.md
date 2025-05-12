# FastAPI Chat Endpoints

This directory contains FastAPI implementations of the chat API endpoints, replacing the previous Next.js implementations.

## Endpoints

The API provides the following endpoints:

### Conversations

- `GET /api/conversations?user_id={user_id}` - Get all active conversations for a specific user
- `POST /api/conversations` - Create a new conversation

### Messages

- `GET /api/messages?conversation_id={conversation_id}` - Get all messages for a specific conversation
- `POST /api/messages` - Create a new message

### Users

- `GET /api/users` - Get all users with transformed data for frontend

## Setup and Running

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Run the API server:

```bash
# On Linux/Mac
python run.py

# On Windows
start_server.bat
```

The server will start on http://localhost:8000 (or the port specified in your .env file)

## API Documentation

Once the server is running, you can access the auto-generated API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

The API uses the following environment variables from the `.env` file:

- `NEXT_PUBLIC_SUPABASE_URL` - Supabase URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `HOST` - Host to run the server on (default: 0.0.0.0)
- `PORT` - Port to run the server on (default: 8000)

You can copy the `.env.example` file to `.env` and update the values:

```bash
cp .env.example .env
```

## Testing

A test script is provided to verify that the API is working correctly. There are two ways to run the tests:

### Option 1: Start server and tests in one step (Windows only)

```bash
start_and_test.bat
```

This script will:
- Start the API server in a new window
- Wait for the server to start
- Run the tests automatically

### Option 2: Start server and tests separately

**Important: The API server must be running before executing the tests.**

1. First, start the API server:
```bash
# On Linux/Mac
python run.py

# On Windows
start_server.bat
```

2. Then, in a separate terminal, run the tests:
```bash
# On Linux/Mac
python test_api.py

# On Windows
run_tests.bat
```

This script will:
1. Check if the API server is running
2. Test the users endpoint
3. Ask for a user ID to test the conversations endpoint
4. Create a new conversation if none exists
5. Test the messages endpoint
6. Create a new test message
