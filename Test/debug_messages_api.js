/**
 * Debug script for the Messages API endpoint
 * This script simulates the behavior of the messages endpoint to identify the specific issue
 */
const axios = require('axios');
const { inspect } = require('util');

// Base URL for the API
const BASE_URL = 'https://waagentv1.onrender.com';

// Function to deeply inspect an object
function deepInspect(obj) {
  return inspect(obj, { depth: null, colors: true });
}

async function debugMessagesAPI() {
  console.log('=== DEBUGGING MESSAGES API ===');
  
  try {
    // Step 1: Get a valid user ID
    console.log('\n1. Getting a valid user ID...');
    const usersResponse = await axios.get(`${BASE_URL}/api/users`);
    const userId = usersResponse.data[0].id;
    console.log(`Using user ID: ${userId}`);
    
    // Step 2: Get a valid conversation ID
    console.log('\n2. Getting a valid conversation ID...');
    const convsResponse = await axios.get(`${BASE_URL}/api/conversations?user_id=${userId}`);
    const conversationId = convsResponse.data[0].id;
    console.log(`Using conversation ID: ${conversationId}`);
    
    // Step 3: Create a test message to ensure the conversation has at least one message
    console.log('\n3. Creating a test message...');
    const newMessage = {
      conversation_id: conversationId,
      content: 'Debug test message',
      message_type: 'text'
    };
    
    const createResponse = await axios.post(`${BASE_URL}/api/messages`, newMessage);
    console.log(`Message created with ID: ${createResponse.data.id}`);
    
    // Step 4: Try to get messages with detailed error handling
    console.log('\n4. Attempting to get messages with detailed error handling...');
    try {
      const messagesResponse = await axios.get(`${BASE_URL}/api/messages?conversation_id=${conversationId}`);
      console.log('GET request succeeded unexpectedly');
      console.log(`Response data: ${deepInspect(messagesResponse.data)}`);
    } catch (error) {
      console.log('GET request failed as expected');
      
      // Detailed error analysis
      console.log('\n5. Detailed error analysis:');
      console.log(`Error name: ${error.name}`);
      console.log(`Error message: ${error.message}`);
      
      if (error.response) {
        console.log(`Status: ${error.response.status}`);
        console.log(`Status text: ${error.response.statusText}`);
        console.log(`Headers: ${deepInspect(error.response.headers)}`);
        console.log(`Data: ${deepInspect(error.response.data)}`);
      }
      
      if (error.request) {
        console.log('Request was made but no response was received');
        console.log(`Request: ${deepInspect(error.request)}`);
      }
      
      console.log(`Error config: ${deepInspect(error.config)}`);
    }
    
    // Step 5: Test with a non-existent conversation ID to see if the error is different
    console.log('\n6. Testing with a non-existent conversation ID...');
    const fakeId = '00000000-0000-0000-0000-000000000000';
    try {
      const fakeResponse = await axios.get(`${BASE_URL}/api/messages?conversation_id=${fakeId}`);
      console.log(`Fake ID request succeeded unexpectedly with status: ${fakeResponse.status}`);
    } catch (error) {
      console.log(`Fake ID request failed with status: ${error.response?.status || 'Unknown'}`);
      console.log(`Error data: ${deepInspect(error.response?.data || {})}`);
    }
    
  } catch (error) {
    console.log('❌ Error in debug process:');
    console.log(`Error type: ${error.name}`);
    console.log(`Error message: ${error.message}`);
    
    if (error.response) {
      console.log(`Status: ${error.response.status}`);
      console.log(`Response data: ${deepInspect(error.response.data)}`);
    }
  }
  
  console.log('\n=== DEBUGGING COMPLETED ===');
}

// Run the debug function
debugMessagesAPI();
