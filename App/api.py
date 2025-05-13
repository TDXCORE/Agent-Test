import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import dependencies
from App.DB.supabase_client import get_supabase_client

# Import API routers
from App.Api.conversations import router as conversations_router
from App.Api.messages import router as messages_router
from App.Api.users import router as users_router

# Import webhook handler
from App.Services.simple_webhook import app as webhook_app

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

# Include API routers
app.include_router(conversations_router, prefix="/api/conversations", tags=["conversations"])
app.include_router(messages_router, prefix="/api/messages", tags=["messages"])
app.include_router(users_router, prefix="/api/users", tags=["users"])

# Mount the webhook app
# This will route all requests to /webhook to the webhook_app
from fastapi.middleware.wsgi import WSGIMiddleware
app.mount("/webhook", WSGIMiddleware(webhook_app))

@app.get("/")
async def root():
    return {"message": "Welcome to the Chat API"}

@app.on_event("startup")
async def startup_event():
    # Initialize Supabase client on startup
    logger.info("Initializing Supabase client")
    get_supabase_client()
    
    # Log successful initialization
    logger.info("API initialized successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("App.api:app", host="0.0.0.0", port=8000, reload=True)
