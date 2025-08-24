#!/bin/bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

# Script to view Allure test reports
# Opens the Allure UI in the default browser

set -euo pipefail

# Configuration
ALLURE_UI_BASE="http://localhost:5252"
ALLURE_API_URL="http://localhost:5050"
PROJECT_ID="${PROJECT_ID:-default}"
ALLURE_UI_URL="$ALLURE_UI_BASE/allure-docker-service-ui/projects/$PROJECT_ID"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Allure Test Report Viewer ===${NC}\n"

# Check if services are running
if ! docker compose ps | grep -q "git-reporter-allure.*Up.*healthy"; then
    echo -e "${YELLOW}⚠️  Allure service is not running or unhealthy${NC}"
    echo "Starting services..."
    docker compose up -d
    echo "Waiting for services to start..."
    sleep 10
fi

# Get report status
echo -e "${BLUE}Checking report status...${NC}"
REPORT_URL="$ALLURE_API_URL/allure-docker-service/projects/$PROJECT_ID/reports/latest/index.html"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$REPORT_URL")

if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Report is available${NC}\n"
    
    # Display URLs
    echo -e "${GREEN}Report Access URLs:${NC}"
    echo -e "  ${BLUE}Allure UI Project:${NC} $ALLURE_UI_URL"
    echo -e "  ${BLUE}Allure UI Home:${NC}    $ALLURE_UI_BASE"
    echo -e "  ${BLUE}Direct Report:${NC}     $REPORT_URL"
    echo -e "  ${BLUE}API Endpoint:${NC}      $ALLURE_API_URL/allure-docker-service"
    echo ""
    
    # Try to open in browser
    echo -e "${GREEN}Opening Allure UI in browser...${NC}"
    if command -v xdg-open > /dev/null; then
        xdg-open "$ALLURE_UI_URL" 2>/dev/null
    elif command -v open > /dev/null; then
        open "$ALLURE_UI_URL"
    else
        echo -e "${YELLOW}Could not auto-open browser. Please manually navigate to:${NC}"
        echo "  $ALLURE_UI_URL"
    fi
    
    echo -e "\n${GREEN}Tips:${NC}"
    echo "  • The UI auto-refreshes every 3 seconds when new results are added"
    echo "  • The report opens directly to the '$PROJECT_ID' project"
    echo "  • Use the timeline view to see test execution over time"
    echo "  • Categories show test results grouped by status"
    echo "  • Click 'LATEST' button to see the most recent test run"
else
    echo -e "${YELLOW}⚠️  No report found. Run some tests first:${NC}"
    echo "  uv run pytest --alluredir=allure-results"
    echo ""
    echo "Or if you have existing results, wait a few seconds for auto-generation."
fi