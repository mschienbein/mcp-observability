#!/bin/bash

echo "================================="
echo "Enable AWS Bedrock for LibreChat"
echo "================================="
echo ""

# Get the task role ARN
TASK_ROLE=$(aws cloudformation describe-stack-resources --stack-name LibreChatStack --query "StackResources[?LogicalResourceId=='LibreChatTaskDefTaskRole5B06068B'].PhysicalResourceId" --output text)

if [ -z "$TASK_ROLE" ]; then
    echo "Error: Could not find LibreChat task role. Is the stack deployed?"
    exit 1
fi

echo "Found task role: $TASK_ROLE"
echo ""
echo "Adding Bedrock permissions..."

# Create and attach Bedrock policy
aws iam put-role-policy --role-name "$TASK_ROLE" --policy-name "BedrockAccess" --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:ListFoundationModels",
                "bedrock:GetFoundationModel"
            ],
            "Resource": "*"
        }
    ]
}' 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Bedrock permissions added successfully!"
    echo ""
    echo "Available Bedrock models in us-east-1:"
    echo "  • Claude 3 Opus, Sonnet, Haiku"
    echo "  • Claude Instant"
    echo "  • Llama 2 70B"
    echo "  • Titan Text"
    echo "  • Jurassic-2"
    echo "  • Command"
    echo ""
    echo "LibreChat will automatically use your AWS credentials for Bedrock."
    echo "No API key needed!"
else
    echo "❌ Failed to add Bedrock permissions"
fi