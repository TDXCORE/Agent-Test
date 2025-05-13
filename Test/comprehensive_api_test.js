/**
 * Comprehensive API Testing Script
 * 
 * This script tests all endpoints of the WA Agent API and provides detailed error reporting.
 * It includes tests for:
 * - Users API
 * - Conversations API
 * - Messages API (with multiple approaches to help debug the order parameter issue)
 * 
 * Usage: node comprehensive_api_test.js
 */

const axios = require('axios');
const { inspect } = require('util');

// Base URL for the API
const BASE_URL = 'https://waagentv1.onrender.com';

// Function to deeply inspect an object for better debugging
function deepInspect(obj) {
  return inspect(obj, { depth: null, colors: true });
}

// Function to format the test result
function formatTestResult(name, success, details = {}) {
  const status = success ? '✅ PASSED' : '❌ FAILED';
  console.log(`\n${name}: ${status}`);
  
  if (details.status) console.log(`Status: ${details.status}`);
  if (details.message) console.log(`Message: ${details.message}`);
  if (details.data) console.log(`Data: ${JSON.stringify(details.data, null, 2)}`);
  
  return { name, success, details };
}

// Main testing function
async function testAllEndpoints() {
  console.log('=== COMPREHENSIVE API TESTING ===');
  console.log(`Testing against: ${BASE_URL}`);
  console.log('Started at:', new Date().toLocaleString());
  console.log('-----------------------------------');
  
  const results = [];
  let userId = null;
  let conversationId = null;
  
  // Test 1: Users API
  console.log('\n=== Testing Users API ===');
  try {
    console.log(`GET request to: ${BASE_URL}/api/users`);
    const usersResponse = await axios.get(`${BASE_URL}/api/users`);
    
    console.log(`Status: ${usersResponse.status}`);
    console.log(`Response data: ${JSON.stringify(usersResponse.data, null, 2)}`);
    
    if (usersResponse.data && usersResponse.data.length > 0) {
      userId = usersResponse.data[0].id;
      console.log(`✅ Users API test passed. Retrieved ${usersResponse.data.length} users.`);
      console.log(`Using user ID: ${userId} for conversation test`);
      
      results.push(formatTestResult('Users API', true, {
        status: usersResponse.status,
        data: { count: usersResponse.data.length, sample: usersResponse.data[0] }
      }));
    } else {
      console.log('❌ Users API test failed. No users returned.');
      results.push(formatTestResult('Users API', false, {
        status: usersResponse.status,
        message: 'No users returned'
      }));
    }
  } catch (error) {
    console.log('❌ Users API test failed.');
    console.log(`Error: ${error.message}`);
    
    if (error.response) {
      console.log(`Status: ${error.response.status}`);
      console.log(`Response data: ${JSON.stringify(error.response.data, null, 2)}`);
    }
    
    results.push(formatTestResult('Users API', false, {
      status: error.response?.status,
      message: error.message,
      data: error.response?.data
    }));
  }
  
  // Test 2: Conversations API (only if we have a user ID)
  if (userId) {
    console.log('\n=== Testing Conversations API ===');
    try {
      console.log(`GET request to: ${BASE_URL}/api/conversations?user_id=${userId}`);
      const convsResponse = await axios.get(`${BASE_URL}/api/conversations?user_id=${userId}`);
      
      console.log(`Status: ${convsResponse.status}`);
      console.log(`Response data: ${JSON.stringify(convsResponse.data, null, 2)}`);
      
      if (convsResponse.data && convsResponse.data.length > 0) {
        conversationId = convsResponse.data[0].id;
        console.log(`✅ Conversations API test passed. Retrieved ${convsResponse.data.length} conversations.`);
        console.log(`Using conversation ID: ${conversationId} for messages test`);
        
        results.push(formatTestResult('Conversations API', true, {
          status: convsResponse.status,
          data: { count: convsResponse.data.length, sample: convsResponse.data[0] }
        }));
      } else {
        console.log('❌ Conversations API test failed. No conversations returned.');
        results.push(formatTestResult('Conversations API', false, {
          status: convsResponse.status,
          message: 'No conversations returned'
        }));
      }
    } catch (error) {
      console.log('❌ Conversations API test failed.');
      console.log(`Error: ${error.message}`);
      
      if (error.response) {
        console.log(`Status: ${error.response.status}`);
        console.log(`Response data: ${JSON.stringify(error.response.data, null, 2)}`);
      }
      
      results.push(formatTestResult('Conversations API', false, {
        status: error.response?.status,
        message: error.message,
        data: error.response?.data
      }));
    }
  }
  
  // Test 3: Messages API - Standard approach (only if we have a conversation ID)
  if (conversationId) {
    console.log('\n=== Testing Messages API (Standard) ===');
    try {
      console.log(`GET request to: ${BASE_URL}/api/messages?conversation_id=${conversationId}`);
      const messagesResponse = await axios.get(`${BASE_URL}/api/messages?conversation_id=${conversationId}`);
      
      console.log(`Status: ${messagesResponse.status}`);
      console.log(`Response data: ${JSON.stringify(messagesResponse.data, null, 2)}`);
      
      console.log(`✅ Messages API (Standard) test passed. Retrieved ${messagesResponse.data.length} messages.`);
      
      results.push(formatTestResult('Messages API (Standard)', true, {
        status: messagesResponse.status,
        data: { count: messagesResponse.data.length }
      }));
    } catch (error) {
      console.log('❌ Messages API (Standard) test failed.');
      console.log(`Error: ${error.message}`);
      
      if (error.response) {
        console.log(`Status: ${error.response.status}`);
        console.log(`Response data: ${JSON.stringify(error.response.data, null, 2)}`);
      }
      
      results.push(formatTestResult('Messages API (Standard)', false, {
        status: error.response?.status,
        message: error.message,
        data: error.response?.data
      }));
    }
    
    // Test 4: Messages API - Create a new message
    console.log('\n=== Testing Messages API (Create) ===');
    try {
      const newMessage = {
        conversation_id: conversationId,
        content: 'Test message from comprehensive API test script',
        message_type: 'text'
      };
      
      console.log(`POST request to: ${BASE_URL}/api/messages`);
      console.log(`Request data: ${JSON.stringify(newMessage, null, 2)}`);
      
      const createResponse = await axios.post(`${BASE_URL}/api/messages`, newMessage);
      
      console.log(`Status: ${createResponse.status}`);
      console.log(`Response data: ${JSON.stringify(createResponse.data, null, 2)}`);
      
      console.log('✅ Messages API (Create) test passed.');
      
      results.push(formatTestResult('Messages API (Create)', true, {
        status: createResponse.status,
        data: createResponse.data
      }));
    } catch (error) {
      console.log('❌ Messages API (Create) test failed.');
      console.log(`Error: ${error.message}`);
      
      if (error.response) {
        console.log(`Status: ${error.response.status}`);
        console.log(`Response data: ${JSON.stringify(error.response.data, null, 2)}`);
      }
      
      results.push(formatTestResult('Messages API (Create)', false, {
        status: error.response?.status,
        message: error.message,
        data: error.response?.data
      }));
    }
  }
  
  // Print test summary
  console.log('\n=== TEST SUMMARY ===');
  results.forEach(result => {
    console.log(`${result.name}: ${result.success ? '✅ PASSED' : '❌ FAILED'}`);
    if (!result.success && result.details.data) {
      console.log(`  Error: ${JSON.stringify(result.details.data, null, 2)}`);
    }
  });
  
  // Provide analysis and recommendations
  console.log('\n=== ANALYSIS AND RECOMMENDATIONS ===');
  
  // Check if we had the specific order() error
  const messagesApiResult = results.find(r => r.name === 'Messages API (Standard)');
  if (messagesApiResult && !messagesApiResult.success) {
    const errorData = messagesApiResult.details.data;
    
    if (errorData && errorData.detail && errorData.detail.includes('BaseSelectRequestBuilder.order() takes 2 positional arguments but 3 were given')) {
      console.log('ISSUE IDENTIFIED: The Messages API is failing due to an incorrect order() method call.');
      console.log('RECOMMENDATION: Update the order() method in App/Api/messages.py line ~80 from:');
      console.log('  .order("created_at", {"ascending": True})');
      console.log('To one of these alternatives:');
      console.log('  1. .order("created_at")  # Default is ascending');
      console.log('  2. .order("created_at", desc=False)  # Explicitly set ascending');
      console.log('  3. .order("created_at asc")  # SQL-style syntax');
    } else {
      console.log('The Messages API is failing, but not with the expected order() parameter error.');
      console.log('Check the error details above for more information.');
    }
  }
  
  console.log('\nTest completed at:', new Date().toLocaleString());
}

// Run the tests
testAllEndpoints().catch(error => {
  console.error('Unhandled error in test script:', error.message);
});
