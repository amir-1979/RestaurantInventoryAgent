# 🚀 AWS Deployment Guide

## 📋 Overview

This guide shows you how to deploy the Restaurant Inventory Dashboard to AWS using multiple approaches.

## 🎯 Deployment Options

### Option 1: Static HTML Dashboard + Lambda API (Recommended)
### Option 2: Streamlit on ECS/Fargate
### Option 3: EC2 with Streamlit

---

## 🔥 Option 1: Static Dashboard + Lambda (RECOMMENDED)

### Step 1: Deploy Lambda Function

#### 1.1 Create Lambda Deployment Package
```bash
# Create deployment directory
mkdir lambda_deployment
cd lambda_deployment

# Copy Lambda function
cp ../lambda_inventory_agent.py .

# Install dependencies
pip install -r ../requirements_lambda.txt -t .

# Create deployment package
zip -r inventory_lambda.zip .
```

#### 1.2 Create Lambda Function in AWS Console
1. **Go to AWS Lambda Console**
2. **Click "Create function"**
3. **Choose "Author from scratch"**
4. **Function name:** `inventory-analyzer`
5. **Runtime:** Python 3.9 or 3.10
6. **Upload** the `inventory_lambda.zip` file

#### 1.3 Configure Lambda Environment
- **Timeout:** 5 minutes
- **Memory:** 512 MB
- **Environment Variables:**
  - `INVENTORY_BUCKET`: your-bucket-name

#### 1.4 Create API Gateway
1. **Go to API Gateway Console**
2. **Create REST API**
3. **Create Resource:** `/analyze`
4. **Create Method:** POST
5. **Integration Type:** Lambda Function
6. **Lambda Function:** inventory-analyzer
7. **Enable CORS**
8. **Deploy API**

### Step 2: Deploy Static Dashboard to S3

#### 2.1 Create S3 Bucket
```bash
# Create bucket (replace with unique name)
aws s3 mb s3://your-inventory-dashboard-bucket

# Enable static website hosting
aws s3 website s3://your-inventory-dashboard-bucket \
  --index-document static_dashboard.html
```

#### 2.2 Update HTML File
Edit `static_dashboard.html` and replace:
```javascript
const LAMBDA_API_URL = 'YOUR_LAMBDA_API_GATEWAY_URL_HERE';
```
With your actual API Gateway URL.

#### 2.3 Upload Files to S3
```bash
# Upload HTML file
aws s3 cp static_dashboard.html s3://your-inventory-dashboard-bucket/

# Upload inventory CSV
aws s3 cp inventory.csv s3://your-inventory-dashboard-bucket/

# Make files public
aws s3api put-object-acl --bucket your-inventory-dashboard-bucket \
  --key static_dashboard.html --acl public-read
```

#### 2.4 Configure Bucket Policy
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-inventory-dashboard-bucket/*"
        }
    ]
}
```

### Step 3: Access Your Dashboard
Your dashboard will be available at:
```
http://your-inventory-dashboard-bucket.s3-website-region.amazonaws.com
```

---

## 🐳 Option 2: Streamlit on ECS/Fargate

### Step 1: Create Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "simple_secure_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Step 2: Build and Push to ECR
```bash
# Create ECR repository
aws ecr create-repository --repository-name inventory-dashboard

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t inventory-dashboard .

# Tag image
docker tag inventory-dashboard:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/inventory-dashboard:latest

# Push image
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/inventory-dashboard:latest
```

### Step 3: Create ECS Service
1. **Go to ECS Console**
2. **Create Cluster** (Fargate)
3. **Create Task Definition**
   - **Image URI:** Your ECR image URI
   - **Port:** 8501
   - **Memory:** 2GB
   - **CPU:** 1 vCPU
4. **Create Service**
5. **Configure Load Balancer** (ALB)

---

## 🖥️ Option 3: EC2 with Streamlit

### Step 1: Launch EC2 Instance
1. **AMI:** Amazon Linux 2
2. **Instance Type:** t3.medium
3. **Security Group:** Allow HTTP (80), HTTPS (443), SSH (22)

### Step 2: Setup Instance
```bash
# Connect to instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Install Python and dependencies
sudo yum update -y
sudo yum install python3 python3-pip git -y

# Clone your repository
git clone your-repo-url
cd your-repo

# Install requirements
pip3 install -r requirements.txt

# Install nginx
sudo yum install nginx -y

# Start streamlit
nohup streamlit run simple_secure_dashboard.py --server.port=8501 &

# Configure nginx reverse proxy
sudo nano /etc/nginx/nginx.conf
```

### Step 3: Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## 🔧 Quick Setup Commands

### For Lambda + S3 (Fastest)
```bash
# 1. Create Lambda package
mkdir lambda_deploy && cd lambda_deploy
cp ../lambda_inventory_agent.py .
pip install pandas boto3 -t .
zip -r lambda.zip .

# 2. Create S3 bucket
aws s3 mb s3://my-inventory-dashboard-$(date +%s)
aws s3 website s3://my-inventory-dashboard-$(date +%s) --index-document static_dashboard.html

# 3. Upload files
aws s3 cp ../static_dashboard.html s3://my-inventory-dashboard-$(date +%s)/
aws s3 cp ../inventory.csv s3://my-inventory-dashboard-$(date +%s)/
```

### For ECS (Docker)
```bash
# 1. Build and push
docker build -t inventory-dashboard .
# (Follow ECR steps above)

# 2. Deploy via ECS Console
# (Follow ECS steps above)
```

---

## 💰 Cost Estimates

### Lambda + S3 (Recommended)
- **S3:** ~$0.50/month
- **Lambda:** ~$1-5/month (depending on usage)
- **API Gateway:** ~$1-3/month
- **Total:** ~$2-8/month

### ECS Fargate
- **Fargate:** ~$15-30/month
- **Load Balancer:** ~$20/month
- **Total:** ~$35-50/month

### EC2
- **t3.medium:** ~$30/month
- **Total:** ~$30/month

---

## 🔒 Security Considerations

### For Production:
1. **Enable HTTPS** (use CloudFront + ACM)
2. **Use Cognito** for authentication
3. **Enable WAF** for protection
4. **Use VPC** for network isolation
5. **Enable CloudTrail** for auditing

### Quick Security Setup:
```bash
# Enable CloudFront for HTTPS
aws cloudfront create-distribution --distribution-config file://cloudfront-config.json

# Enable WAF
aws wafv2 create-web-acl --name inventory-dashboard-waf --scope CLOUDFRONT
```

---

## 🚀 Recommended Deployment Path

1. **Start with Option 1** (Lambda + S3) - cheapest and easiest
2. **Use the static HTML dashboard** - works immediately
3. **Upload your inventory.csv to S3**
4. **Test with sample data first**
5. **Add real Lambda integration later**

The static dashboard works standalone and you can add the Lambda backend when ready!

---

## 📞 Support

If you need help:
1. Check AWS CloudWatch logs
2. Verify S3 bucket permissions
3. Test Lambda function separately
4. Check API Gateway CORS settings

**Quick Test URLs:**
- S3 Static Site: `http://bucket-name.s3-website-region.amazonaws.com`
- API Gateway: `https://api-id.execute-api.region.amazonaws.com/stage/analyze`