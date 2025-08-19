#!/bin/bash

echo "================================="
echo "LibreChat Secret Configuration"
echo "================================="
echo ""
echo "This script will securely store your API keys in AWS Secrets Manager"
echo "NEVER commit API keys to git or share them in chat!"
echo ""

# Get the secret ARN
SECRET_ARN=$(aws secretsmanager describe-secret --secret-id $(aws cloudformation describe-stack-resources --stack-name LibreChatStack --query "StackResources[?LogicalResourceId=='LibreChatSecrets'].PhysicalResourceId" --output text) --query "ARN" --output text 2>/dev/null)

if [ -z "$SECRET_ARN" ]; then
    echo "Error: Could not find LibreChat secrets in AWS. Is the stack deployed?"
    exit 1
fi

echo "Found secret: $SECRET_ARN"
echo ""

# Function to update a secret field
update_secret_field() {
    local field_name=$1
    local field_value=$2
    
    # Get current secret
    CURRENT_SECRET=$(aws secretsmanager get-secret-value --secret-id "$SECRET_ARN" --query "SecretString" --output text)
    
    # Update the field using jq
    UPDATED_SECRET=$(echo "$CURRENT_SECRET" | jq --arg key "$field_name" --arg val "$field_value" '.[$key] = $val')
    
    # Update in AWS
    aws secretsmanager update-secret --secret-id "$SECRET_ARN" --secret-string "$UPDATED_SECRET" > /dev/null 2>&1
    
    echo "✅ Updated $field_name"
}

# Menu for updating secrets
while true; do
    echo ""
    echo "What would you like to configure?"
    echo "1. OpenAI API Key"
    echo "2. Anthropic API Key"
    echo "3. Google AI API Key"
    echo "4. AWS Bedrock Credentials"
    echo "5. Azure OpenAI Credentials"
    echo "6. View current configuration (without secrets)"
    echo "7. Exit"
    echo ""
    read -p "Select option (1-7): " choice
    
    case $choice in
        1)
            echo "Enter your OpenAI API Key (starts with sk-):"
            read -s OPENAI_KEY
            echo ""
            if [[ $OPENAI_KEY == sk-* ]]; then
                update_secret_field "OPENAI_API_KEY" "$OPENAI_KEY"
            else
                echo "❌ Invalid OpenAI key format"
            fi
            ;;
        2)
            echo "Enter your Anthropic API Key:"
            read -s ANTHROPIC_KEY
            echo ""
            update_secret_field "ANTHROPIC_API_KEY" "$ANTHROPIC_KEY"
            ;;
        3)
            echo "Enter your Google AI API Key:"
            read -s GOOGLE_KEY
            echo ""
            update_secret_field "GOOGLE_API_KEY" "$GOOGLE_KEY"
            ;;
        4)
            echo "AWS Bedrock uses IAM role credentials automatically."
            echo "No API key needed if running on AWS!"
            echo ""
            echo "To enable Bedrock, ensure your ECS task role has bedrock:InvokeModel permission."
            ;;
        5)
            echo "Enter your Azure OpenAI Endpoint:"
            read AZURE_ENDPOINT
            echo "Enter your Azure OpenAI API Key:"
            read -s AZURE_KEY
            echo ""
            update_secret_field "AZURE_OPENAI_ENDPOINT" "$AZURE_ENDPOINT"
            update_secret_field "AZURE_OPENAI_API_KEY" "$AZURE_KEY"
            ;;
        6)
            echo "Current configuration:"
            aws secretsmanager get-secret-value --secret-id "$SECRET_ARN" --query "SecretString" --output text | jq 'keys[]' | while read key; do
                echo "  - $key: [CONFIGURED]"
            done
            ;;
        7)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid option"
            ;;
    esac
done