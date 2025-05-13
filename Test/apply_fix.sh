#!/bin/bash
# Script to automatically apply the fix to the Messages API

# Set colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}===== MESSAGES API FIX SCRIPT =====${NC}"
echo "This script will automatically fix the order() method issue in App/Api/messages.py"
echo

# Check if the file exists
if [ ! -f "App/Api/messages.py" ]; then
    echo -e "${RED}Error: App/Api/messages.py not found${NC}"
    echo "Make sure you're running this script from the root directory of your project"
    exit 1
fi

# Check if the file contains the problematic line
if ! grep -q '.order("created_at", {"ascending": True}).execute()' "App/Api/messages.py"; then
    echo -e "${YELLOW}Warning: Could not find the problematic line in App/Api/messages.py${NC}"
    echo "The file may have already been fixed or the line might be different"
    echo "Would you like to continue anyway? (y/n)"
    read -r response
    if [[ "$response" != "y" ]]; then
        echo "Aborting"
        exit 0
    fi
fi

# Create a backup of the original file
echo "Creating backup of original file..."
cp "App/Api/messages.py" "App/Api/messages.py.bak"
echo -e "${GREEN}Backup created at App/Api/messages.py.bak${NC}"

# Apply the fix
echo "Applying fix..."
sed -i 's/.order("created_at", {"ascending": True}).execute()/.order("created_at").execute()/g' "App/Api/messages.py"

# Check if the fix was applied
if grep -q '.order("created_at").execute()' "App/Api/messages.py"; then
    echo -e "${GREEN}Fix successfully applied!${NC}"
else
    echo -e "${RED}Failed to apply fix${NC}"
    echo "Restoring backup..."
    cp "App/Api/messages.py.bak" "App/Api/messages.py"
    echo "Backup restored"
    exit 1
fi

echo
echo -e "${YELLOW}===== NEXT STEPS =====${NC}"
echo "1. Restart your API server"
echo "2. Test the Messages API to verify the fix"
echo "   You can use one of the test scripts:"
echo "   - node Test/comprehensive_api_test.js"
echo "   - node Test/fix_messages_api_test.js"
echo "   - node Test/api_fix_solution.js"
echo
echo -e "${GREEN}Done!${NC}"
