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

class ConversationWithUnread(Conversation):
    unread_count: int = 0
    agent_enabled: bool = True

@router.get("/", response_model=List[ConversationWithUnread])
@router.get("", response_model=List[ConversationWithUnread])  # Ruta sin barra final
async def get_conversations(
    user_id: str = Query(..., description="User ID to fetch conversations for"),
    supabase = Depends(get_supabase)
):
    """
    Get all active conversations for a specific user with unread message count
    """
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Get all conversations for the user
        response = supabase.table("conversations").select(
            "id, external_id, platform, status, created_at, updated_at, agent_enabled"
        ).eq("user_id", user_id).eq("status", "active").execute()
        
        # Check for errors
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error fetching conversations: {response.error}")
            raise HTTPException(status_code=500, detail=str(response.error))
        
        # Get unread message counts for each conversation
        conversations_with_unread = []
        for conv in response.data:
            # Count unread messages where role is 'user' (from WhatsApp)
            unread_query = supabase.table("messages").select(
                "id", "count"
            ).eq("conversation_id", conv["id"]).eq("role", "user").eq("read", False).execute()
            
            unread_count = 0
            if unread_query.data and len(unread_query.data) > 0:
                unread_count = unread_query.data[0].get("count", 0)
            
            # Add unread count to conversation data
            conv_with_unread = {
                **conv, 
                "unread_count": unread_count,
                "agent_enabled": conv.get("agent_enabled", True)  # Default to True if not set
            }
            conversations_with_unread.append(conv_with_unread)
        
        return conversations_with_unread
    
    except Exception as e:
        logger.error(f"Error in conversations API: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.post("/", response_model=Conversation, status_code=201)
@router.post("", response_model=Conversation, status_code=201)  # Ruta sin barra final
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

@router.put("/{conversation_id}/agent", status_code=200)
async def toggle_agent(
    conversation_id: str,
    enable: bool = Query(..., description="True to enable agent, False to disable"),
    supabase = Depends(get_supabase)
):
    """
    Enable or disable the agent for a specific conversation
    """
    try:
        if not conversation_id:
            raise HTTPException(status_code=400, detail="conversation_id is required")
        
        logger.info(f"{'Enabling' if enable else 'Disabling'} agent for conversation: {conversation_id}")
        
        # Update agent status in the conversation
        response = supabase.table("conversations").update(
            {"agent_enabled": enable, "updated_at": "now()"}
        ).eq("id", conversation_id).execute()
        
        # Check for errors
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error updating agent status: {response.error}")
            raise HTTPException(status_code=500, detail=str(response.error))
        
        # Return success response
        return {
            "success": True, 
            "conversation_id": conversation_id, 
            "agent_enabled": enable
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error updating agent status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
