/**
 * API Fix Solution Script
 * 
 * This script provides a comprehensive solution for the API issues:
 * 1. Tests all API endpoints to identify issues
 * 2. Generates a fixed version of the messages.py file
 * 3. Provides clear instructions on how to apply the fix
 * 
 * Usage: node api_fix_solution.js
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');
const { inspect } = require('util');

// Base URL for the API
const BASE_URL = 'https://waagentv1.onrender.com';

// Function to deeply inspect an object for better debugging
function deepInspect(obj) {
  return inspect(obj, { depth: null, colors: true });
}

// Function to print a section header
function printHeader(title) {
  console.log('\n' + '='.repeat(title.length + 10));
  console.log(`===== ${title} =====`);
  console.log('='.repeat(title.length + 10));
}

// Main function to test and fix the API issues
async function testAndFixAPI() {
  printHeader('API FIX SOLUTION');
  console.log(`Testing against: ${BASE_URL}`);
  console.log('Started at:', new Date().toLocaleString());
  
  // Step 1: Test the Users API
  printHeader('STEP 1: TEST USERS API');
  let userId = null;
  try {
    console.log(`GET request to: ${BASE_URL}/api/users`);
    const usersResponse = await axios.get(`${BASE_URL}/api/users`);
    
    console.log(`Status: ${usersResponse.status}`);
    console.log(`Found ${usersResponse.data.length} users`);
    
    if (usersResponse.data && usersResponse.data.length > 0) {
      userId = usersResponse.data[0].id;
      console.log(`✅ Users API test passed. Using user ID: ${userId}`);
    } else {
      console.log('❌ Users API test failed. No users returned.');
      return;
    }
  } catch (error) {
    console.log('❌ Users API test failed.');
    console.log(`Error: ${error.message}`);
    
    if (error.response) {
      console.log(`Status: ${error.response.status}`);
      console.log(`Response data: ${JSON.stringify(error.response.data, null, 2)}`);
    }
    return;
  }
  
  // Step 2: Test the Conversations API
  printHeader('STEP 2: TEST CONVERSATIONS API');
  let conversationId = null;
  try {
    console.log(`GET request to: ${BASE_URL}/api/conversations?user_id=${userId}`);
    const convsResponse = await axios.get(`${BASE_URL}/api/conversations?user_id=${userId}`);
    
    console.log(`Status: ${convsResponse.status}`);
    console.log(`Found ${convsResponse.data.length} conversations`);
    
    if (convsResponse.data && convsResponse.data.length > 0) {
      conversationId = convsResponse.data[0].id;
      console.log(`✅ Conversations API test passed. Using conversation ID: ${conversationId}`);
    } else {
      console.log('❌ Conversations API test failed. No conversations returned.');
      return;
    }
  } catch (error) {
    console.log('❌ Conversations API test failed.');
    console.log(`Error: ${error.message}`);
    
    if (error.response) {
      console.log(`Status: ${error.response.status}`);
      console.log(`Response data: ${JSON.stringify(error.response.data, null, 2)}`);
    }
    return;
  }
  
  // Step 3: Test the Messages API
  printHeader('STEP 3: TEST MESSAGES API');
  let messagesApiError = null;
  try {
    console.log(`GET request to: ${BASE_URL}/api/messages?conversation_id=${conversationId}`);
    const messagesResponse = await axios.get(`${BASE_URL}/api/messages?conversation_id=${conversationId}`);
    
    console.log(`Status: ${messagesResponse.status}`);
    console.log(`Found ${messagesResponse.data.length} messages`);
    console.log(`✅ Messages API test passed unexpectedly.`);
    
    // If we get here, the API is working, which is unexpected based on the error
    console.log('\n⚠️ NOTE: The Messages API is working now, which is different from the previous error.');
    console.log('This could mean:');
    console.log('1. The issue has been fixed');
    console.log('2. The issue is intermittent');
    console.log('3. The issue only occurs under certain conditions');
    
    // Even though the test passed, we'll still generate the fix for reference
    console.log('\nGenerating the fix anyway for reference...');
  } catch (error) {
    console.log('❌ Messages API test failed as expected.');
    console.log(`Error: ${error.message}`);
    
    if (error.response) {
      console.log(`Status: ${error.response.status}`);
      console.log(`Response data: ${JSON.stringify(error.response.data, null, 2)}`);
      messagesApiError = error.response.data;
    }
  }
  
  // Step 4: Generate the fix
  printHeader('STEP 4: GENERATE FIX');
  
  // Check if we have the specific order() error
  const hasOrderError = messagesApiError && 
                        messagesApiError.detail && 
                        messagesApiError.detail.includes('BaseSelectRequestBuilder.order() takes 2 positional arguments but 3 were given');
  
  if (hasOrderError) {
    console.log('✅ Confirmed the specific order() error.');
  } else {
    console.log('⚠️ Could not confirm the specific order() error, but generating fix anyway.');
  }
  
  // Generate the fixed messages.py file
  console.log('\nGenerating fixed messages.py file...');
  
  // The original problematic line
  const originalLine = '.order("created_at", {"ascending": True}).execute()';
  
  // The fixed line
  const fixedLine = '.order("created_at").execute()';
  
  // Create the fixed file content
  const fixedContent = `# FIXED VERSION OF messages.py
# 
# This file contains the fixed version of the messages.py file with the correct order() method.
# The original file is located at App/Api/messages.py
# 
# The fix changes:
#   .order("created_at", {"ascending": True}).execute()
# To:
#   .order("created_at").execute()
#
# This fixes the error: "BaseSelectRequestBuilder.order() takes 2 positional arguments but 3 were given"

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
        
        logger.info(f"Creating message for conversation: {message.conversation_id}")
        
        # Add message to the conversation
        try:
            response = supabase.table("messages").insert({
                "conversation_id": message.conversation_id,
                "role": "user",  # Messages from the web interface are always from the user
                "content": message.content,
                "message_type": message.message_type,
                "media_url": message.media_url
            }).execute()
            logger.info("Message insert request executed")
        except Exception as db_error:
            logger.error(f"Database error creating message: {str(db_error)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        
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
`;

  // Write the fixed file
  const fixedFilePath = 'Test/fixed_messages.py';
  try {
    fs.writeFileSync(fixedFilePath, fixedContent);
    console.log(`✅ Fixed file written to: ${fixedFilePath}`);
  } catch (error) {
    console.log(`❌ Error writing fixed file: ${error.message}`);
  }
  
  // Step 5: Provide instructions
  printHeader('STEP 5: INSTRUCTIONS');
  console.log('To fix the Messages API issue, follow these steps:');
  console.log('\n1. Locate the file App/Api/messages.py in your project');
  console.log('\n2. Find the line containing:');
  console.log(`   ${originalLine}`);
  console.log('\n3. Replace it with:');
  console.log(`   ${fixedLine}`);
  console.log('\n4. Save the file and restart your API server');
  console.log('\nAlternatively, you can use the fixed file that was generated:');
  console.log(`1. Copy the content from ${fixedFilePath}`);
  console.log('2. Replace the content of App/Api/messages.py with it');
  console.log('3. Restart your API server');
  
  printHeader('SOLUTION COMPLETED');
  console.log('Completed at:', new Date().toLocaleString());
}

// Run the test and fix function
testAndFixAPI().catch(error => {
  console.error('Unhandled error in solution script:', error.message);
});
