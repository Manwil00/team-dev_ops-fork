#!/bin/bash

# Script to update EC2 security group with GitHub Actions IP ranges
# Usage: ./update-security-group.sh <security-group-id> <aws-region>

SECURITY_GROUP_ID=$1
AWS_REGION=$2

if [ -z "$SECURITY_GROUP_ID" ] || [ -z "$AWS_REGION" ]; then
    echo "Usage: $0 <security-group-id> <aws-region>"
    echo "Example: $0 sg-1234567890abcdef0 us-east-1"
    exit 1
fi

# Get GitHub Actions IP ranges
echo "Fetching GitHub Actions IP ranges..."
GITHUB_IPS=$(curl -s https://api.github.com/meta | jq -r '.actions[]')

# Remove existing SSH rules for GitHub Actions (if any)
echo "Removing existing SSH rules..."
aws ec2 describe-security-groups \
    --group-ids $SECURITY_GROUP_ID \
    --region $AWS_REGION \
    --query 'SecurityGroups[0].IpPermissions[?FromPort==`22`].IpRanges[].CidrIp' \
    --output text | while read cidr; do
    if [ "$cidr" != "None" ] && [ ! -z "$cidr" ]; then
        echo "Removing rule for $cidr"
        aws ec2 revoke-security-group-ingress \
            --group-id $SECURITY_GROUP_ID \
            --protocol tcp \
            --port 22 \
            --cidr $cidr \
            --region $AWS_REGION || true
    fi
done

# Add new SSH rules for GitHub Actions IP ranges
echo "Adding new SSH rules for GitHub Actions..."
for ip in $GITHUB_IPS; do
    echo "Adding rule for $ip"
    aws ec2 authorize-security-group-ingress \
        --group-id $SECURITY_GROUP_ID \
        --protocol tcp \
        --port 22 \
        --cidr $ip \
        --region $AWS_REGION
done

echo "Security group update completed!"
echo "Don't forget to also allow SSH from your own IP for manual access." 