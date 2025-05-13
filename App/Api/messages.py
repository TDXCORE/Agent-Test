from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime

# Import dependencies from the new structure
from App.dependencies import get_supabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Define models
class MessageCreate(BaseModel):
    conversation_id: str
    content: str
    message_type: str = "text"
    media_url: Optional[str] = None

class Message(BaseModel):
    id: str
    types: str
    text: str
    time: str
    message_type: str
    media_url: Optional[str] = None

class MessageDB(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: str
    message_type: str
    media_url: Optional[str] = None

@router.get("/", response_model=List[Message])
async def get_messages(
    conversation_id: str = Query(..., description="Conversation ID to fetch messages for"),
    supabase = Depends(get_supabase)
):
    """
    Get all messages for a specific conversation
    """
    try:
        if not conversation_id:
            raise HTTPException(status_code=400, detail="conversation_id is required")
        
        # Get all messages for the conversation
        response = supabase.table("messages").select(
            "*"
        ).eq("conversation_id", conversation_id).order("created_at", {"ascending": True}).execute()
        
        # Check for errors
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error fetching messages: {response.error}")
            raise HTTPException(status_code=500, detail=str(response.error))
        
        # Transform data for frontend
        messages = []
        for msg in response.data:
            created_at = datetime.fromisoformat(msg["created_at"].replace("Z", "+00:00"))
            messages.append({
                "id": msg["id"],
                "types": "sent" if msg["role"] == "user" else "received",
                "text": msg["content"],
                "time": created_at.strftime("%I:%M %p"),  # Format as hour:minute AM/PM
                "message_type": msg["message_type"],
                "media_url": msg["media_url"]
            })
        
        return messages
    
    except Exception as e:
        logger.error(f"Error in messages API: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/", response_model=Message, status_code=201)
async def create_message(
    message: MessageCreate,
    supabase = Depends(get_supabase)
):
    """
    Create a new message
    """
    try:
        if not message.conversation_id or not message.content:
            raise HTTPException(status_code=400, detail="conversation_id and content are required")
        
        # Add message to the conversation
        response = supabase.table("messages").insert({
            "conversation_id": message.conversation_id,
            "role": "user",  # Messages from the web interface are always from the user
            "content": message.content,
            "message_type": message.message_type,
            "media_url": message.media_url
        }).execute()
        
        # Check for errors
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error creating message: {response.error}")
            raise HTTPException(status_code=500, detail=str(response.error))
        
        # Transform for frontend
        created_msg = response.data[0]
        created_at = datetime.fromisoformat(created_msg["created_at"].replace("Z", "+00:00"))
        
        return {
            "id": created_msg["id"],
            "types": "sent",
            "text": created_msg["content"],
            "time": created_at.strftime("%I:%M %p"),  # Format as hour:minute AM/PM
            "message_type": created_msg["message_type"],
            "media_url": created_msg["media_url"]
        }
    
    except Exception as e:
        logger.error(f"Error in messages API: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
