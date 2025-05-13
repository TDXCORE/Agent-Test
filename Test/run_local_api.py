"""
Script to run a local version of the API for testing purposes.
This will help us test our changes to the messages endpoint.
"""
import sys
import os
import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

# Add the parent directory to the path so we can import from App
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the API routers
from App.Api.messages import router as messages_router
from App.Api.conversations import router as conversations_router
from App.Api.users import router as users_router

# Create a FastAPI app
app = FastAPI(title="Local API Test")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a main router
main_router = APIRouter()

# Add the API routers
app.include_router(messages_router, prefix="/api/messages", tags=["messages"])
app.include_router(conversations_router, prefix="/api/conversations", tags=["conversations"])
app.include_router(users_router, prefix="/api/users", tags=["users"])

# Add a root endpoint
@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Local API Test is running",
        "endpoints": {
            "messages": "/api/messages",
            "conversations": "/api/conversations",
            "users": "/api/users"
        }
    }

if __name__ == "__main__":
    print("Starting local API test server...")
    print("API will be available at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
