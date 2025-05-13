/**
 * API Testing and Fixing Index Script
 * 
 * This script serves as a central entry point for all the API testing and fixing scripts.
 * It provides a menu-based interface to run the appropriate script based on the user's needs.
 * 
 * Usage: node Test/api_test_index.js
 */

const { spawn } = require('child_process');
const readline = require('readline');
const fs = require('fs');
const path = require('path');

// Create readline interface for user input
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Function to clear the console
function clearConsole() {
  // For Windows
  if (process.platform === 'win32') {
    process.stdout.write('\x1Bc');
  } 
  // For Unix-like systems
  else {
    console.clear();
  }
}

// Function to display a header
function displayHeader(title) {
  console.log('='.repeat(title.length + 10));
  console.log(`===== ${title} =====`);
  console.log('='.repeat(title.length + 10));
  console.log();
}

// Function to run a script
function runScript(scriptPath) {
  clearConsole();
  console.log(`Running ${scriptPath}...\n`);
  
  const child = spawn('node', [scriptPath], { stdio: 'inherit' });
  
  child.on('close', (code) => {
    console.log(`\nScript exited with code ${code}`);
    console.log('\nPress Enter to return to the menu...');
    
    // Wait for user to press Enter
    rl.question('', () => {
      displayMenu();
    });
  });
}

// Function to run a shell script
function runShellScript(scriptPath) {
  clearConsole();
  console.log(`Running ${scriptPath}...\n`);
  
  let command, args;
  
  // For Windows
  if (process.platform === 'win32') {
    if (scriptPath.endsWith('.bat')) {
      command = scriptPath;
      args = [];
    } else {
      command = 'sh';
      args = [scriptPath];
    }
  } 
  // For Unix-like systems
  else {
    command = 'sh';
    args = [scriptPath];
  }
  
  const child = spawn(command, args, { stdio: 'inherit' });
  
  child.on('close', (code) => {
    console.log(`\nScript exited with code ${code}`);
    console.log('\nPress Enter to return to the menu...');
    
    // Wait for user to press Enter
    rl.question('', () => {
      displayMenu();
    });
  });
}

// Function to display the README
function displayReadme() {
  clearConsole();
  
  try {
    const readmePath = path.join(__dirname, 'API_TESTING_README.md');
    const readme = fs.readFileSync(readmePath, 'utf8');
    console.log(readme);
  } catch (error) {
    console.log('Error reading README file:', error.message);
  }
  
  console.log('\nPress Enter to return to the menu...');
  
  // Wait for user to press Enter
  rl.question('', () => {
    displayMenu();
  });
}

// Function to display the menu
function displayMenu() {
  clearConsole();
  displayHeader('API TESTING AND FIXING MENU');
  
  console.log('1. Run Comprehensive API Test');
  console.log('   - Tests all API endpoints and provides detailed error reporting');
  console.log();
  
  console.log('2. Run Fix Messages API Test');
  console.log('   - Specifically diagnoses the Messages API issue and provides recommendations');
  console.log();
  
  console.log('3. Run API Fix Solution');
  console.log('   - Provides a complete solution including a fixed version of the messages.py file');
  console.log();
  
  console.log('4. Apply Fix (Unix/Linux/macOS)');
  console.log('   - Automatically applies the fix using the shell script');
  console.log();
  
  console.log('5. Apply Fix (Windows)');
  console.log('   - Automatically applies the fix using the batch script');
  console.log();
  
  console.log('6. View API Testing README');
  console.log('   - Displays the README file with detailed information about the scripts');
  console.log();
  
  console.log('0. Exit');
  console.log();
  
  rl.question('Enter your choice: ', (choice) => {
    switch (choice) {
      case '1':
        runScript(path.join(__dirname, 'comprehensive_api_test.js'));
        break;
      case '2':
        runScript(path.join(__dirname, 'fix_messages_api_test.js'));
        break;
      case '3':
        runScript(path.join(__dirname, 'api_fix_solution.js'));
        break;
      case '4':
        runShellScript(path.join(__dirname, 'apply_fix.sh'));
        break;
      case '5':
        runShellScript(path.join(__dirname, 'apply_fix.bat'));
        break;
      case '6':
        displayReadme();
        break;
      case '0':
        clearConsole();
        console.log('Exiting...');
        rl.close();
        break;
      default:
        console.log('Invalid choice. Please try again.');
        setTimeout(displayMenu, 1000);
        break;
    }
  });
}

// Start the menu
displayMenu();
