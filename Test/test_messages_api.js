/**
 * Test script for the Messages API endpoint
 * This script tests the functionality of the Messages API with detailed error reporting
 */
const axios = require('axios');

// Base URL for the API
const BASE_URL = 'https://waagentv1.onrender.com';

async function testMessagesAPI() {
  console.log('=== TESTING MESSAGES API IN DETAIL ===');
  
  // Obtain a valid conversation ID first
  try {
    console.log('\n1. Getting a valid user ID...');
    const usersResponse = await axios.get(`${BASE_URL}/api/users`);
    
    if (usersResponse.status !== 200 || !usersResponse.data.length) {
      console.log('❌ Failed to get users');
      console.log(`Status: ${usersResponse.status}`);
      console.log(`Response: ${JSON.stringify(usersResponse.data, null, 2)}`);
      return;
    }
    
    const userId = usersResponse.data[0].id;
    console.log(`✅ Successfully retrieved users`);
    console.log(`Using user ID: ${userId}`);
    
    console.log('\n2. Getting a valid conversation ID for this user...');
    const convsResponse = await axios.get(`${BASE_URL}/api/conversations?user_id=${userId}`);
    
    if (convsResponse.status !== 200 || !convsResponse.data.length) {
      console.log('❌ Failed to get conversations');
      console.log(`Status: ${convsResponse.status}`);
      console.log(`Response: ${JSON.stringify(convsResponse.data, null, 2)}`);
      return;
    }
    
    const conversationId = convsResponse.data[0].id;
    console.log(`✅ Successfully retrieved conversations`);
    console.log(`Using conversation ID: ${conversationId}`);
    
    // Test GET messages endpoint
    console.log('\n3. Testing GET messages with valid conversation ID...');
    try {
      const messagesResponse = await axios.get(`${BASE_URL}/api/messages?conversation_id=${conversationId}`);
      console.log(`✅ Messages API GET request successful`);
      console.log(`Status: ${messagesResponse.status}`);
      console.log(`Response data (first 2 messages):`);
      
      if (messagesResponse.data && messagesResponse.data.length > 0) {
        const sampleData = messagesResponse.data.slice(0, 2);
        console.log(JSON.stringify(sampleData, null, 2));
        console.log(`Total messages: ${messagesResponse.data.length}`);
      } else {
        console.log('No messages found for this conversation');
      }
    } catch (error) {
      console.log('❌ Messages API GET request failed');
      console.log(`Status: ${error.response?.status || 'Unknown'}`);
      console.log(`Error: ${error.message}`);
      
      if (error.response?.data) {
        console.log(`Response data: ${JSON.stringify(error.response.data, null, 2)}`);
      }
      
      // Try with additional debugging
      console.log('\n4. Testing GET messages with additional debugging...');
      try {
        // Make a request with a timeout to ensure we get a complete response
        const debugResponse = await axios.get(
          `${BASE_URL}/api/messages?conversation_id=${conversationId}`, 
          { timeout: 10000 }
        );
        console.log(`Debug request succeeded unexpectedly`);
        console.log(`Status: ${debugResponse.status}`);
      } catch (debugError) {
        console.log(`Debug request failed as expected`);
        console.log(`Status: ${debugError.response?.status || 'Unknown'}`);
        console.log(`Error type: ${debugError.name}`);
        console.log(`Error message: ${debugError.message}`);
        
        if (debugError.response?.data) {
          console.log(`Response data: ${JSON.stringify(debugError.response.data, null, 2)}`);
        }
      }
    }
    
    // Test POST messages endpoint
    console.log('\n5. Testing POST a new message...');
    try {
      const newMessage = {
        conversation_id: conversationId,
        content: 'Test message from API test script',
        message_type: 'text'
      };
      
      const createResponse = await axios.post(`${BASE_URL}/api/messages`, newMessage);
      console.log(`✅ Messages API POST request successful`);
      console.log(`Status: ${createResponse.status}`);
      console.log(`Response data: ${JSON.stringify(createResponse.data, null, 2)}`);
      
      // Verify the message was created by trying to get messages again
      console.log('\n6. Verifying message creation by getting messages again...');
      try {
        const verifyResponse = await axios.get(`${BASE_URL}/api/messages?conversation_id=${conversationId}`);
        console.log(`✅ Verification GET request successful`);
        console.log(`Status: ${verifyResponse.status}`);
        console.log(`Total messages after creation: ${verifyResponse.data.length}`);
      } catch (verifyError) {
        console.log('❌ Verification GET request failed');
        console.log(`Status: ${verifyError.response?.status || 'Unknown'}`);
        console.log(`Error: ${verifyError.message}`);
      }
    } catch (error) {
      console.log('❌ Messages API POST request failed');
      console.log(`Status: ${error.response?.status || 'Unknown'}`);
      console.log(`Error: ${error.message}`);
      
      if (error.response?.data) {
        console.log(`Response data: ${JSON.stringify(error.response.data, null, 2)}`);
      }
    }
    
  } catch (error) {
    console.log('❌ Error in test setup:');
    console.log(`Error type: ${error.name}`);
    console.log(`Error message: ${error.message}`);
    
    if (error.response) {
      console.log(`Status: ${error.response.status}`);
      console.log(`Response data: ${JSON.stringify(error.response.data, null, 2)}`);
    }
  }
  
  console.log('\n=== MESSAGES API TEST COMPLETED ===');
}

// Run the test
testMessagesAPI();
