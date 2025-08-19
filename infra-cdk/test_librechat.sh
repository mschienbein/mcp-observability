#!/bin/bash

# Test LibreChat deployment

echo "Testing LibreChat deployment..."
echo "================================"

# Get ALB URL
ALB_URL=$(aws cloudformation describe-stacks --stack-name LibreChatStack --query "Stacks[0].Outputs[?OutputKey=='LibreChatServiceLoadBalancerDNS'].OutputValue" --output text 2>/dev/null)

if [ -z "$ALB_URL" ]; then
    echo "Error: Could not find ALB URL. Stack may not be deployed."
    exit 1
fi

echo "LibreChat URL: http://$ALB_URL"
echo ""

# Test health endpoint
echo "Testing health endpoint..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$ALB_URL/health" 2>/dev/null)

if [ "$HEALTH_STATUS" = "200" ]; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed. Status: $HEALTH_STATUS"
fi

echo ""
echo "Testing main page..."
MAIN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://$ALB_URL/" 2>/dev/null)

if [ "$MAIN_STATUS" = "200" ] || [ "$MAIN_STATUS" = "302" ]; then
    echo "✅ Main page accessible!"
else
    echo "❌ Main page not accessible. Status: $MAIN_STATUS"
fi

echo ""
echo "================================"
echo "You can access LibreChat at: http://$ALB_URL"
echo "Default configuration:"
echo "  - Registration is enabled"
echo "  - Users provide their own API keys"
echo "  - MongoDB and Meilisearch are running internally"