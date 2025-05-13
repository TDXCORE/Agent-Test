from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import logging

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
class ConversationCreate(BaseModel):
    user_id: str
    external_id: str
    platform: str = "web"

class Conversation(BaseModel):
    id: str
    external_id: str
    platform: str
    status: str
    created_at: str
    updated_at: str

@router.get("/", response_model=List[Conversation])
async def get_conversations(
    user_id: str = Query(..., description="User ID to fetch conversations for"),
    supabase = Depends(get_supabase)
):
    """
    Get all active conversations for a specific user
    """
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Get all conversations for the user
        response = supabase.table("conversations").select(
            "id, external_id, platform, status, created_at, updated_at"
        ).eq("user_id", user_id).eq("status", "active").execute()
        
        # Check for errors
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error fetching conversations: {response.error}")
            raise HTTPException(status_code=500, detail=str(response.error))
        
        # Return the data
        return response.data
    
    except Exception as e:
        logger.error(f"Error in conversations API: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/", response_model=Conversation, status_code=201)
async def create_conversation(
    conversation: ConversationCreate,
    supabase = Depends(get_supabase)
):
    """
    Create a new conversation
    """
    try:
        if not conversation.user_id or not conversation.external_id:
            raise HTTPException(status_code=400, detail="user_id and external_id are required")
        
        # Create a new conversation
        response = supabase.table("conversations").insert({
            "user_id": conversation.user_id,
            "external_id": conversation.external_id,
            "platform": conversation.platform,
            "status": "active"
        }).execute()
        
        # Check for errors
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error creating conversation: {response.error}")
            raise HTTPException(status_code=500, detail=str(response.error))
        
        # Return the created conversation
        return response.data[0]
    
    except Exception as e:
        logger.error(f"Error in conversations API: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
