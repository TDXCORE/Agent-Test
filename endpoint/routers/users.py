from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import random
import sys
import os

# Add parent directory to path to import dependencies
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dependencies import get_supabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Define models
class Avatar(BaseModel):
    type: str
    variant: str
    title: str

class Contact(BaseModel):
    id: str
    name: str
    avatar: Avatar
    status: str
    lastChat: str
    time: str
    unread: int

@router.get("/", response_model=List[Contact])
async def get_users(
    supabase = Depends(get_supabase)
):
    """
    Get all users with transformed data for frontend
    """
    try:
        # Get all users from Supabase
        response = supabase.table("users").select(
            "id, full_name, phone, email, company, created_at"
        ).execute()
        
        # Check for errors
        if hasattr(response, 'error') and response.error:
            logger.error(f"Error fetching users: {response.error}")
            raise HTTPException(status_code=500, detail=str(response.error))
        
        # Transform data for frontend
        contacts = []
        variants = ["primary", "secondary", "success", "danger", "warning", "info"]
        
        for user in response.data:
            # Generate avatar data
            first_letter = user["full_name"][0].upper() if user["full_name"] else 'U'
            variant = variants[hash(user["id"]) % len(variants)]  # Deterministic variant based on user ID
            
            # Format time
            created_at = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
            formatted_time = created_at.strftime("%I:%M %p")  # Format as hour:minute AM/PM
            
            contacts.append({
                "id": user["id"],
                "name": user["full_name"],
                "avatar": {
                    "type": "init",
                    "variant": variant,
                    "title": first_letter
                },
                "status": "offline",  # Default status
                "lastChat": "Click to start conversation",
                "time": formatted_time,
                "unread": 0
            })
        
        return contacts
    
    except Exception as e:
        logger.error(f"Error in users API: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
