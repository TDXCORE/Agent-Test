from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import logging
import uuid
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

# Add endpoint to mark messages as read
@router.put("/read", status_code=200)
@router.put("read", status_code=200)  # Ruta sin barra final
async def mark_messages_as_read(
    conversation_id: str = Query(..., description="Conversation ID to mark messages as read"),
    supabase = Depends(get_supabase)
):
    """
    Mark all messages in a conversation as read
    """
    try:
        if not conversation_id:
            raise HTTPException(status_code=400, detail="conversation_id is required")
        
        logger.info(f"Marking messages as read for conversation: {conversation_id}")
        
        # Update all unread messages in the conversation
        response = supabase.table("messages").update(
            {"read": True}
        ).eq("conversation_id", conversation_id).eq("read", False).execute()
        
        # Check for errors
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error marking messages as read: {response.error}")
            raise HTTPException(status_code=500, detail=str(response.error))
        
        # Return success response
        return {"success": True, "updated_count": len(response.data) if response.data else 0}
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error marking messages as read: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

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
@router.get("", response_model=List[Message])  # Ruta sin barra final
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
        
        logger.info(f"Fetching messages for conversation: {conversation_id}")
        
        # Get all messages for the conversation
        try:
            response = supabase.table("messages").select(
                "*"
            ).eq("conversation_id", conversation_id).order("created_at").execute()
            logger.info(f"Supabase response received with {len(response.data) if hasattr(response, 'data') else 'no'} messages")
        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        
        # Check for errors
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error fetching messages: {response.error}")
            raise HTTPException(status_code=500, detail=str(response.error))
        
        # Check if response.data exists and is a list
        if not hasattr(response, 'data') or not isinstance(response.data, list):
            error_msg = f"Invalid response format: {type(response)}, has data: {hasattr(response, 'data')}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        # If no messages found, return empty list
        if len(response.data) == 0:
            logger.info(f"No messages found for conversation: {conversation_id}")
            return []
        
        # Transform data for frontend
        messages = []
        try:
            for msg in response.data:
                logger.debug(f"Processing message: {msg.get('id', 'unknown')}")
                
                # Safely get required fields with defaults
                msg_id = msg.get('id', str(uuid.uuid4()))
                role = msg.get('role', 'system')
                content = msg.get('content', '(No content)')
                message_type = msg.get('message_type', 'text')
                media_url = msg.get('media_url')
                
                # Handle created_at date safely
                try:
                    if 'created_at' in msg and msg['created_at']:
                        created_at_str = msg['created_at']
                        # Handle different date formats
                        if 'Z' in created_at_str:
                            created_at_str = created_at_str.replace('Z', '+00:00')
                        elif '+' not in created_at_str and '-' in created_at_str:
                            # Add timezone if missing
                            created_at_str = created_at_str + '+00:00'
                        
                        created_at = datetime.fromisoformat(created_at_str)
                        time_str = created_at.strftime("%I:%M %p")
                    else:
                        time_str = datetime.now().strftime("%I:%M %p")
                except Exception as date_error:
                    logger.warning(f"Error parsing date: {str(date_error)}, using current time")
                    time_str = datetime.now().strftime("%I:%M %p")
                
                messages.append({
                    "id": msg_id,
                    "types": "sent" if role == "user" else "received",
                    "text": content,
                    "time": time_str,
                    "message_type": message_type,
                    "media_url": media_url
                })
            logger.info(f"Successfully transformed {len(messages)} messages")
        except Exception as transform_error:
            logger.error(f"Error transforming message data: {str(transform_error)}", exc_info=True)
            # Continue with any messages we were able to transform
            if not messages:
                # If we couldn't transform any messages, return an error
                raise HTTPException(status_code=500, detail=f"Error transforming data: {str(transform_error)}")
            else:
                # If we have some messages, log the error but return what we have
                logger.warning(f"Returning {len(messages)} messages despite transformation errors")
        
        return messages
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in messages API: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post("/", response_model=Message, status_code=201)
@router.post("", response_model=Message, status_code=201)  # Ruta sin barra final
async def create_message(
    message: MessageCreate,
    supabase = Depends(get_supabase)
):
    """
    Create a new message and send it to WhatsApp if it's from the frontend
    """
    try:
        if not message.conversation_id or not message.content:
            raise HTTPException(status_code=400, detail="conversation_id and content are required")
        
        logger.info(f"Creating message for conversation: {message.conversation_id}")
        
        # Get conversation to check if it's a WhatsApp conversation
        conversation_response = supabase.table("conversations").select(
            "*"
        ).eq("id", message.conversation_id).execute()
        
        if not conversation_response.data or len(conversation_response.data) == 0:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conversation = conversation_response.data[0]
        
        # Add message to the conversation
        try:
            response = supabase.table("messages").insert({
                "conversation_id": message.conversation_id,
                "role": "assistant",  # Messages from the web interface are from the assistant
                "content": message.content,
                "message_type": message.message_type,
                "media_url": message.media_url,
                "read": True  # Messages sent from frontend are already read
            }).execute()
            logger.info("Message insert request executed")
        except Exception as db_error:
            logger.error(f"Database error creating message: {str(db_error)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        
        # If it's a WhatsApp conversation, send the message to WhatsApp
        if conversation["platform"] == "whatsapp":
            from App.Services.whatsapp_api import send_whatsapp_message
            
            # Get the phone number from external_id
            phone = conversation["external_id"]
            
            # Send message to WhatsApp
            send_result = send_whatsapp_message(
                to=phone,
                message_type=message.message_type,
                content=message.content,
                caption=None
            )
            
            logger.info(f"Message sent to WhatsApp: {send_result is not None}")
        
        # Check for errors
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error creating message: {response.error}")
            raise HTTPException(status_code=500, detail=str(response.error))
        
        # Check if response.data exists and has at least one item
        if not hasattr(response, 'data') or not isinstance(response.data, list) or len(response.data) == 0:
            error_msg = f"Invalid response format after creating message: {type(response)}, has data: {hasattr(response, 'data')}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Transform for frontend
        try:
            created_msg = response.data[0]
            created_at = datetime.fromisoformat(created_msg["created_at"].replace("Z", "+00:00"))
            
            result = {
                "id": created_msg["id"],
                "types": "sent",
                "text": created_msg["content"],
                "time": created_at.strftime("%I:%M %p"),  # Format as hour:minute AM/PM
                "message_type": created_msg["message_type"],
                "media_url": created_msg.get("media_url")
            }
            logger.info(f"Message created successfully with ID: {created_msg['id']}")
            return result
        except Exception as transform_error:
            logger.error(f"Error transforming created message data: {str(transform_error)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error transforming data: {str(transform_error)}")
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
