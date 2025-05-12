import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
import sys
import logging
from dotenv import load_dotenv

# Import dependencies
from dependencies import get_supabase

# Import routers
from routers import conversations, messages, users

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Chat API",
    description="API for chat application using FastAPI and Supabase",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(messages.router, prefix="/api/messages", tags=["messages"])
app.include_router(users.router, prefix="/api/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Chat API"}

@app.on_event("startup")
async def startup_event():
    # Initialize Supabase client on startup
    logger.info("Initializing Supabase client")
    # Import here to avoid circular imports
    from supabase_client import get_supabase_client
    get_supabase_client()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
