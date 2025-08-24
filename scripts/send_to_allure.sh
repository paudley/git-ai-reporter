#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

# Script to send test results to Allure Docker Service
# This script collects all allure-results and sends them to the running Allure service

set -euo pipefail

# Configuration
ALLURE_URL="${ALLURE_URL:-http://localhost:5050}"
PROJECT_ID="${PROJECT_ID:-default}"
RESULTS_DIR="${RESULTS_DIR:-allure-results}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Sending Allure results to Docker service...${NC}"

# Check if results directory exists
if [ ! -d "$RESULTS_DIR" ]; then
    echo -e "${RED}Error: Results directory '$RESULTS_DIR' not found${NC}"
    exit 1
fi

# Check if there are any results
RESULT_COUNT=$(find "$RESULTS_DIR" -name "*.json" -o -name "*.txt" -o -name "*.xml" 2>/dev/null | wc -l)
if [ "$RESULT_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}Warning: No results found in '$RESULTS_DIR'${NC}"
    exit 0
fi

echo "Found $RESULT_COUNT result files"

# Build curl command with all files
echo -e "${YELLOW}Sending results to Allure service...${NC}"

# Build the curl command dynamically
CURL_CMD="curl -X POST \"$ALLURE_URL/allure-docker-service/send-results?project_id=$PROJECT_ID\" -H \"Content-Type: multipart/form-data\""

# Add each file as a form field
for file in "$RESULTS_DIR"/*; do
    if [ -f "$file" ]; then
        CURL_CMD="$CURL_CMD -F \"files[]=@$file\""
    fi
done

CURL_CMD="$CURL_CMD -s -w \"\nHTTP_STATUS:%{http_code}\" 2>/dev/null || echo \"FAILED\""

# Execute the curl command
RESPONSE=$(eval $CURL_CMD)

# Check response
if echo "$RESPONSE" | grep -q "HTTP_STATUS:200"; then
    echo -e "${GREEN}✓ Results successfully sent to Allure${NC}"
    
    # Get the report URL
    echo -e "\n${GREEN}Report URLs:${NC}"
    echo "  UI Project View: http://localhost:5252/allure-docker-service-ui/projects/$PROJECT_ID"
    echo "  Direct Report:   $ALLURE_URL/allure-docker-service/projects/$PROJECT_ID/reports/latest/index.html"
    echo ""
    echo -e "${GREEN}To view the report:${NC}"
    echo "  1. Open http://localhost:5252/allure-docker-service-ui/projects/$PROJECT_ID in your browser"
    echo "  2. Or directly access the report at the Direct Report URL above"
else
    echo -e "${RED}✗ Failed to send results to Allure${NC}"
    echo "Response: $RESPONSE"
    exit 1
fi

# Optional: Clean allure-results after successful send
read -p "Do you want to clean the allure-results directory? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "${RESULTS_DIR:?}/"*
    echo -e "${GREEN}✓ Cleaned allure-results directory${NC}"
fi