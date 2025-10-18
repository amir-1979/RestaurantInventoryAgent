#!/bin/bash

# 🚀 One-Click AWS Deployment Script for Restaurant Inventory Dashboard
# This script deploys everything you need to AWS

set -e  # Exit on any error

echo "🍽️ Restaurant Inventory Dashboard - AWS Deployment"
echo "=================================================="

# Configuration
STACK_NAME="inventory-dashboard-stack"
BUCKET_PREFIX="inventory-dashboard"
REGION="us-east-1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run 'aws configure' first."
        exit 1
    fi
    
    # Check required files
    required_files=("lambda_inventory_agent.py" "static_dashboard.html" "inventory.csv" "cloudformation_template.yaml")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file '$file' not found."
            exit 1
        fi
    done
    
    log_success "Prerequisites check passed!"
}

# Create Lambda deployment package
create_lambda_package() {
    log_info "Creating Lambda deployment package..."
    
    # Create temporary directory
    mkdir -p lambda_deploy
    cd lambda_deploy
    
    # Copy Lambda function
    cp ../lambda_inventory_agent.py .
    
    # Install dependencies
    pip install pandas==2.0.3 boto3==1.28.62 -t . --quiet
    
    # Create ZIP package
    zip -r lambda_package.zip . > /dev/null
    
    cd ..
    
    log_success "Lambda package created!"
}

# Deploy CloudFormation stack
deploy_infrastructure() {
    log_info "Deploying AWS infrastructure..."
    
    # Generate unique bucket name
    TIMESTAMP=$(date +%s)
    UNIQUE_BUCKET_NAME="${BUCKET_PREFIX}-${TIMESTAMP}"
    
    # Deploy CloudFormation stack
    aws cloudformation deploy \
        --template-file cloudformation_template.yaml \
        --stack-name $STACK_NAME \
        --parameter-overrides BucketName=$UNIQUE_BUCKET_NAME \
        --capabilities CAPABILITY_IAM \
        --region $REGION
    
    log_success "Infrastructure deployed!"
    
    # Get stack outputs
    BUCKET_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
        --output text \
        --region $REGION)
    
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`APIGatewayURL`].OutputValue' \
        --output text \
        --region $REGION)
    
    WEBSITE_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`WebsiteURL`].OutputValue' \
        --output text \
        --region $REGION)
    
    CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
        --output text \
        --region $REGION)
    
    # Store for later use
    echo "BUCKET_NAME=$BUCKET_NAME" > deployment_vars.env
    echo "API_URL=$API_URL" >> deployment_vars.env
    echo "WEBSITE_URL=$WEBSITE_URL" >> deployment_vars.env
    echo "CLOUDFRONT_URL=$CLOUDFRONT_URL" >> deployment_vars.env
}

# Update Lambda function code
update_lambda_code() {
    log_info "Updating Lambda function code..."
    
    source deployment_vars.env
    
    LAMBDA_FUNCTION_NAME=$(aws cloudformation describe-stacks \
        --stack-name $STACK_NAME \
        --query 'Stacks[0].Outputs[?OutputKey==`LambdaFunctionName`].OutputValue' \
        --output text \
        --region $REGION)
    
    # Update Lambda function
    aws lambda update-function-code \
        --function-name $LAMBDA_FUNCTION_NAME \
        --zip-file fileb://lambda_deploy/lambda_package.zip \
        --region $REGION > /dev/null
    
    log_success "Lambda function updated!"
}

# Upload files to S3
upload_files() {
    log_info "Uploading files to S3..."
    
    source deployment_vars.env
    
    # Update HTML file with API URL
    sed "s|YOUR_LAMBDA_API_GATEWAY_URL_HERE|$API_URL|g" static_dashboard.html > static_dashboard_updated.html
    
    # Upload files
    aws s3 cp static_dashboard_updated.html s3://$BUCKET_NAME/static_dashboard.html --region $REGION
    aws s3 cp inventory.csv s3://$BUCKET_NAME/ --region $REGION
    
    # Create a simple error page
    echo "<html><body><h1>Error</h1><p>Page not found</p></body></html>" > error.html
    aws s3 cp error.html s3://$BUCKET_NAME/ --region $REGION
    
    log_success "Files uploaded to S3!"
}

# Test deployment
test_deployment() {
    log_info "Testing deployment..."
    
    source deployment_vars.env
    
    # Test website accessibility
    if curl -s --head $WEBSITE_URL | head -n 1 | grep -q "200 OK"; then
        log_success "Website is accessible!"
    else
        log_warning "Website might not be ready yet (can take a few minutes)"
    fi
    
    # Test API Gateway
    if curl -s -X POST $API_URL -H "Content-Type: application/json" -d '{}' | grep -q "error\|result"; then
        log_success "API Gateway is responding!"
    else
        log_warning "API Gateway might not be ready yet"
    fi
}

# Display results
show_results() {
    source deployment_vars.env
    
    echo ""
    echo "🎉 Deployment Complete!"
    echo "======================"
    echo ""
    echo "📊 Your Dashboard URLs:"
    echo "  • Website (HTTP):  $WEBSITE_URL"
    echo "  • CloudFront (HTTPS): $CLOUDFRONT_URL"
    echo ""
    echo "🔧 Technical Details:"
    echo "  • S3 Bucket:       $BUCKET_NAME"
    echo "  • API Gateway:     $API_URL"
    echo "  • Region:          $REGION"
    echo ""
    echo "🔑 Login Credentials:"
    echo "  • admin / admin123"
    echo "  • manager / manager123"
    echo "  • staff / staff123"
    echo ""
    echo "📝 Next Steps:"
    echo "  1. Visit your dashboard URL"
    echo "  2. Login with the credentials above"
    echo "  3. Upload new inventory.csv files to S3 bucket"
    echo "  4. Customize the dashboard as needed"
    echo ""
    echo "💰 Estimated Monthly Cost: \$2-8"
    echo ""
    log_success "Deployment successful! 🚀"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    rm -rf lambda_deploy
    rm -f static_dashboard_updated.html error.html
    log_success "Cleanup complete!"
}

# Main deployment flow
main() {
    echo "Starting deployment process..."
    echo ""
    
    check_prerequisites
    create_lambda_package
    deploy_infrastructure
    update_lambda_code
    upload_files
    test_deployment
    show_results
    cleanup
    
    echo ""
    echo "🎊 All done! Your inventory dashboard is live on AWS!"
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"