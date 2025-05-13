/**
 * Test script to verify that API routes work both with and without trailing slashes
 * 
 * This script tests the following routes:
 * - /api/users (with and without trailing slash)
 * - /api/conversations (with and without trailing slash)
 * - /api/messages (with and without trailing slash)
 */

const axios = require('axios');

// Base URL for the API
const BASE_URL = 'https://waagentv1.onrender.com';

// Test function
async function testApiRoutes() {
  console.log('=== TESTING API ROUTES WITH AND WITHOUT TRAILING SLASHES ===');
  console.log(`Testing against: ${BASE_URL}`);
  console.log(`Started at: ${new Date().toLocaleString()}`);
  console.log('-----------------------------------\n');

  // Get a valid user ID first
  console.log('=== Step 1: Getting a valid user ID ===');
  try {
    const usersResponse = await axios.get(`${BASE_URL}/api/users`);
    console.log(`Users API (without slash) - Status: ${usersResponse.status}`);
    
    if (usersResponse.data && usersResponse.data.length > 0) {
      const userId = usersResponse.data[0].id;
      console.log(`Found user ID: ${userId}\n`);
      
      // Test users API with trailing slash
      console.log('=== Step 2: Testing Users API with trailing slash ===');
      try {
        const usersWithSlashResponse = await axios.get(`${BASE_URL}/api/users/`);
        console.log(`Users API (with slash) - Status: ${usersWithSlashResponse.status}`);
        console.log(`Found ${usersWithSlashResponse.data.length} users\n`);
      } catch (error) {
        console.log(`❌ Users API (with slash) - Error: ${error.message}`);
        if (error.response) {
          console.log(`Status: ${error.response.status}`);
          console.log(`Response: ${JSON.stringify(error.response.data)}\n`);
        }
      }
      
      // Test conversations API without trailing slash
      console.log('=== Step 3: Testing Conversations API without trailing slash ===');
      try {
        const convsResponse = await axios.get(`${BASE_URL}/api/conversations?user_id=${userId}`);
        console.log(`Conversations API (without slash) - Status: ${convsResponse.status}`);
        
        if (convsResponse.data && convsResponse.data.length > 0) {
          console.log(`Found ${convsResponse.data.length} conversations`);
          const conversationId = convsResponse.data[0].id;
          console.log(`Found conversation ID: ${conversationId}\n`);
          
          // Test conversations API with trailing slash
          console.log('=== Step 4: Testing Conversations API with trailing slash ===');
          try {
            const convsWithSlashResponse = await axios.get(`${BASE_URL}/api/conversations/?user_id=${userId}`);
            console.log(`Conversations API (with slash) - Status: ${convsWithSlashResponse.status}`);
            console.log(`Found ${convsWithSlashResponse.data.length} conversations\n`);
          } catch (error) {
            console.log(`❌ Conversations API (with slash) - Error: ${error.message}`);
            if (error.response) {
              console.log(`Status: ${error.response.status}`);
              console.log(`Response: ${JSON.stringify(error.response.data)}\n`);
            }
          }
          
          // Test messages API without trailing slash
          console.log('=== Step 5: Testing Messages API without trailing slash ===');
          try {
            const messagesResponse = await axios.get(`${BASE_URL}/api/messages?conversation_id=${conversationId}`);
            console.log(`Messages API (without slash) - Status: ${messagesResponse.status}`);
            console.log(`Found ${messagesResponse.data.length} messages\n`);
          } catch (error) {
            console.log(`❌ Messages API (without slash) - Error: ${error.message}`);
            if (error.response) {
              console.log(`Status: ${error.response.status}`);
              console.log(`Response: ${JSON.stringify(error.response.data)}\n`);
            }
          }
          
          // Test messages API with trailing slash
          console.log('=== Step 6: Testing Messages API with trailing slash ===');
          try {
            const messagesWithSlashResponse = await axios.get(`${BASE_URL}/api/messages/?conversation_id=${conversationId}`);
            console.log(`Messages API (with slash) - Status: ${messagesWithSlashResponse.status}`);
            console.log(`Found ${messagesWithSlashResponse.data.length} messages\n`);
          } catch (error) {
            console.log(`❌ Messages API (with slash) - Error: ${error.message}`);
            if (error.response) {
              console.log(`Status: ${error.response.status}`);
              console.log(`Response: ${JSON.stringify(error.response.data)}\n`);
            }
          }
          
          // Test POST to messages API without trailing slash
          console.log('=== Step 7: Testing POST to Messages API without trailing slash ===');
          try {
            const newMessage = {
              conversation_id: conversationId,
              content: "Test message from API routes test script",
              message_type: "text"
            };
            
            const createResponse = await axios.post(`${BASE_URL}/api/messages`, newMessage);
            console.log(`POST to Messages API (without slash) - Status: ${createResponse.status}`);
            console.log(`Created message with ID: ${createResponse.data.id}\n`);
          } catch (error) {
            console.log(`❌ POST to Messages API (without slash) - Error: ${error.message}`);
            if (error.response) {
              console.log(`Status: ${error.response.status}`);
              console.log(`Response: ${JSON.stringify(error.response.data)}\n`);
            }
          }
          
          // Test POST to messages API with trailing slash
          console.log('=== Step 8: Testing POST to Messages API with trailing slash ===');
          try {
            const newMessage = {
              conversation_id: conversationId,
              content: "Test message from API routes test script (with slash)",
              message_type: "text"
            };
            
            const createWithSlashResponse = await axios.post(`${BASE_URL}/api/messages/`, newMessage);
            console.log(`POST to Messages API (with slash) - Status: ${createWithSlashResponse.status}`);
            console.log(`Created message with ID: ${createWithSlashResponse.data.id}\n`);
          } catch (error) {
            console.log(`❌ POST to Messages API (with slash) - Error: ${error.message}`);
            if (error.response) {
              console.log(`Status: ${error.response.status}`);
              console.log(`Response: ${JSON.stringify(error.response.data)}\n`);
            }
          }
        } else {
          console.log('No conversations found for this user\n');
        }
      } catch (error) {
        console.log(`❌ Conversations API (without slash) - Error: ${error.message}`);
        if (error.response) {
          console.log(`Status: ${error.response.status}`);
          console.log(`Response: ${JSON.stringify(error.response.data)}\n`);
        }
      }
    } else {
      console.log('No users found\n');
    }
  } catch (error) {
    console.log(`❌ Users API (without slash) - Error: ${error.message}`);
    if (error.response) {
      console.log(`Status: ${error.response.status}`);
      console.log(`Response: ${JSON.stringify(error.response.data)}\n`);
    }
  }
  
  console.log('=== TEST SUMMARY ===');
  console.log(`Completed at: ${new Date().toLocaleString()}`);
  console.log('If all tests passed, you should see successful responses for all API endpoints,');
  console.log('both with and without trailing slashes.');
}

// Run the test
testApiRoutes();
