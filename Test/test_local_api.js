/**
 * Test script for the local API
 * This script tests the functionality of the local API endpoints
 */
const axios = require('axios');

// Base URL for the local API
const BASE_URL = 'http://localhost:8001';

async function testLocalAPI() {
  console.log('=== TESTING LOCAL API ===');
  
  try {
    // Test the root endpoint
    console.log('\n1. Testing root endpoint...');
    const rootResponse = await axios.get(`${BASE_URL}/`);
    console.log(`Status: ${rootResponse.status}`);
    console.log(`Response: ${JSON.stringify(rootResponse.data, null, 2)}`);
    
    // Test the users endpoint
    console.log('\n2. Testing users endpoint...');
    try {
      const usersResponse = await axios.get(`${BASE_URL}/api/users`);
      console.log(`Status: ${usersResponse.status}`);
      console.log(`Found ${usersResponse.data.length} users`);
      
      if (usersResponse.data.length > 0) {
        const userId = usersResponse.data[0].id;
        console.log(`Using user ID: ${userId}`);
        
        // Test the conversations endpoint
        console.log('\n3. Testing conversations endpoint...');
        try {
          const convsResponse = await axios.get(`${BASE_URL}/api/conversations?user_id=${userId}`);
          console.log(`Status: ${convsResponse.status}`);
          console.log(`Found ${convsResponse.data.length} conversations`);
          
          if (convsResponse.data.length > 0) {
            const conversationId = convsResponse.data[0].id;
            console.log(`Using conversation ID: ${conversationId}`);
            
            // Test the messages endpoint (GET)
            console.log('\n4. Testing messages endpoint (GET)...');
            try {
              const messagesResponse = await axios.get(`${BASE_URL}/api/messages?conversation_id=${conversationId}`);
              console.log(`Status: ${messagesResponse.status}`);
              console.log(`Found ${messagesResponse.data.length} messages`);
              
              if (messagesResponse.data.length > 0) {
                console.log(`First message: ${JSON.stringify(messagesResponse.data[0], null, 2)}`);
              }
              
              // Test the messages endpoint (POST)
              console.log('\n5. Testing messages endpoint (POST)...');
              try {
                const newMessage = {
                  conversation_id: conversationId,
                  content: 'Test message from local API test script',
                  message_type: 'text'
                };
                
                const createResponse = await axios.post(`${BASE_URL}/api/messages`, newMessage);
                console.log(`Status: ${createResponse.status}`);
                console.log(`Response: ${JSON.stringify(createResponse.data, null, 2)}`);
                
                // Verify the message was created
                console.log('\n6. Verifying message creation...');
                const verifyResponse = await axios.get(`${BASE_URL}/api/messages?conversation_id=${conversationId}`);
                console.log(`Status: ${verifyResponse.status}`);
                console.log(`Found ${verifyResponse.data.length} messages after creation`);
              } catch (error) {
                console.log(`❌ Error testing messages endpoint (POST): ${error.message}`);
                if (error.response) {
                  console.log(`Status: ${error.response.status}`);
                  console.log(`Response: ${JSON.stringify(error.response.data, null, 2)}`);
                }
              }
            } catch (error) {
              console.log(`❌ Error testing messages endpoint (GET): ${error.message}`);
              if (error.response) {
                console.log(`Status: ${error.response.status}`);
                console.log(`Response: ${JSON.stringify(error.response.data, null, 2)}`);
              }
            }
          } else {
            console.log('No conversations found for this user');
          }
        } catch (error) {
          console.log(`❌ Error testing conversations endpoint: ${error.message}`);
          if (error.response) {
            console.log(`Status: ${error.response.status}`);
            console.log(`Response: ${JSON.stringify(error.response.data, null, 2)}`);
          }
        }
      } else {
        console.log('No users found');
      }
    } catch (error) {
      console.log(`❌ Error testing users endpoint: ${error.message}`);
      if (error.response) {
        console.log(`Status: ${error.response.status}`);
        console.log(`Response: ${JSON.stringify(error.response.data, null, 2)}`);
      }
    }
  } catch (error) {
    console.log(`❌ Error testing root endpoint: ${error.message}`);
    if (error.response) {
      console.log(`Status: ${error.response.status}`);
      console.log(`Response: ${JSON.stringify(error.response.data, null, 2)}`);
    }
    console.log('Make sure the local API is running (python Test/run_local_api.py)');
  }
  
  console.log('\n=== LOCAL API TEST COMPLETED ===');
}

// Run the test
testLocalAPI();
