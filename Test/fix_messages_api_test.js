/**
 * Fix Messages API Test Script
 * 
 * This script specifically focuses on diagnosing and fixing the issue with the Messages API.
 * It provides a detailed analysis of the error and recommendations for fixing it.
 * 
 * The main issue appears to be with the order() method in the Supabase query:
 * .order("created_at", {"ascending": True})
 * 
 * The error suggests this is incorrect: "BaseSelectRequestBuilder.order() takes 2 positional arguments but 3 were given"
 * 
 * Usage: node fix_messages_api_test.js
 */

const axios = require('axios');
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

// Main function to diagnose and fix the Messages API issue
async function diagnoseMessagesAPI() {
  printHeader('MESSAGES API DIAGNOSIS');
  console.log(`Testing against: ${BASE_URL}`);
  console.log('Started at:', new Date().toLocaleString());
  
  let userId = null;
  let conversationId = null;
  
  // Step 1: Get a valid user ID
  printHeader('STEP 1: GET USER ID');
  try {
    console.log(`GET request to: ${BASE_URL}/api/users`);
    const usersResponse = await axios.get(`${BASE_URL}/api/users`);
    
    if (usersResponse.data && usersResponse.data.length > 0) {
      userId = usersResponse.data[0].id;
      console.log(`✅ Successfully retrieved user ID: ${userId}`);
    } else {
      console.log('❌ No users found');
      return;
    }
  } catch (error) {
    console.log('❌ Failed to get users');
    console.log(`Error: ${error.message}`);
    return;
  }
  
  // Step 2: Get a valid conversation ID
  printHeader('STEP 2: GET CONVERSATION ID');
  try {
    console.log(`GET request to: ${BASE_URL}/api/conversations?user_id=${userId}`);
    const convsResponse = await axios.get(`${BASE_URL}/api/conversations?user_id=${userId}`);
    
    if (convsResponse.data && convsResponse.data.length > 0) {
      conversationId = convsResponse.data[0].id;
      console.log(`✅ Successfully retrieved conversation ID: ${conversationId}`);
    } else {
      console.log('❌ No conversations found for this user');
      return;
    }
  } catch (error) {
    console.log('❌ Failed to get conversations');
    console.log(`Error: ${error.message}`);
    return;
  }
  
  // Step 3: Test the Messages API
  printHeader('STEP 3: TEST MESSAGES API');
  try {
    console.log(`GET request to: ${BASE_URL}/api/messages?conversation_id=${conversationId}`);
    const messagesResponse = await axios.get(`${BASE_URL}/api/messages?conversation_id=${conversationId}`);
    
    console.log(`✅ Messages API request succeeded unexpectedly`);
    console.log(`Status: ${messagesResponse.status}`);
    console.log(`Retrieved ${messagesResponse.data.length} messages`);
    
    // If we get here, the API is working, which is unexpected based on the error
    console.log('\n⚠️ NOTE: The Messages API is working now, which is different from the previous error.');
    console.log('This could mean:');
    console.log('1. The issue has been fixed');
    console.log('2. The issue is intermittent');
    console.log('3. The issue only occurs under certain conditions');
    
    return;
  } catch (error) {
    console.log('❌ Messages API request failed as expected');
    
    if (error.response) {
      console.log(`Status: ${error.response.status}`);
      console.log(`Error data: ${JSON.stringify(error.response.data, null, 2)}`);
      
      // Check if it's the specific order() error
      if (error.response.data && 
          error.response.data.detail && 
          error.response.data.detail.includes('BaseSelectRequestBuilder.order() takes 2 positional arguments but 3 were given')) {
        
        // We found the specific error, now we can provide a detailed analysis
        printHeader('ERROR ANALYSIS');
        console.log('The error message indicates an issue with the order() method in the Supabase query.');
        console.log('\nCurrent implementation in App/Api/messages.py (around line 80):');
        console.log('```python');
        console.log('response = supabase.table("messages").select(');
        console.log('    "*"');
        console.log(').eq("conversation_id", conversation_id).order("created_at", {"ascending": True}).execute()');
        console.log('```');
        
        console.log('\nThe error suggests that the order() method is being called incorrectly.');
        console.log('According to the error: "BaseSelectRequestBuilder.order() takes 2 positional arguments but 3 were given"');
        
        printHeader('SOLUTION');
        console.log('Based on the Supabase documentation and the error message, here are the correct ways to use the order() method:');
        console.log('\nOption 1: Use the default ascending order');
        console.log('```python');
        console.log('response = supabase.table("messages").select(');
        console.log('    "*"');
        console.log(').eq("conversation_id", conversation_id).order("created_at").execute()');
        console.log('```');
        
        console.log('\nOption 2: Use the desc parameter (False for ascending, True for descending)');
        console.log('```python');
        console.log('response = supabase.table("messages").select(');
        console.log('    "*"');
        console.log(').eq("conversation_id", conversation_id).order("created_at", desc=False).execute()');
        console.log('```');
        
        console.log('\nOption 3: Use SQL-style syntax');
        console.log('```python');
        console.log('response = supabase.table("messages").select(');
        console.log('    "*"');
        console.log(').eq("conversation_id", conversation_id).order("created_at asc").execute()');
        console.log('```');
        
        printHeader('RECOMMENDED FIX');
        console.log('The simplest fix is to use Option 1:');
        console.log('\nChange:');
        console.log('  .order("created_at", {"ascending": True})');
        console.log('\nTo:');
        console.log('  .order("created_at")');
        
        console.log('\nThis change should be made in App/Api/messages.py around line 80.');
      } else {
        console.log('The error is not the expected order() parameter error.');
        console.log('Check the error details above for more information.');
      }
    } else {
      console.log(`Error: ${error.message}`);
    }
  }
  
  printHeader('DIAGNOSIS COMPLETED');
  console.log('Completed at:', new Date().toLocaleString());
}

// Run the diagnosis
diagnoseMessagesAPI().catch(error => {
  console.error('Unhandled error in diagnosis script:', error.message);
});
