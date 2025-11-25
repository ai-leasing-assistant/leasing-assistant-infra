# Leasing Assistant Infrastructure

Infrastructure-as-code for deploying the AI Leasing Assistant platform using Terraform. Manages Lambda functions, DynamoDB, networking, monitoring, and API Gateway across dev, staging, and production environments.

## 🏗️ Architecture Overview

The Leasing Assistant platform is built on AWS serverless architecture:

- **Lambda Functions**: Python-based serverless compute for assistant logic
- **DynamoDB**: NoSQL database for property and tenant data
- **API Gateway**: RESTful API endpoints
- **CloudWatch**: Logging and monitoring
- **VPC**: Network isolation and security

## 📁 Project Structure

```
leasing-assistant-infra/
├── modules/              # Reusable Terraform modules
│   ├── api/             # API Gateway module
│   ├── dynamodb/        # DynamoDB tables module
│   ├── lambda/          # Lambda function module
│   ├── monitoring/      # CloudWatch/alerting module
│   └── network/         # VPC/networking module
│
├── envs/                # Environment-specific configurations
│   ├── dev/            # Development environment
│   ├── staging/        # Staging environment
│   └── prod/           # Production environment
│
├── diagrams/           # Architecture diagrams
│   ├── architecture.png
│   └── cost-breakdown.md
│
├── scripts/            # Helper scripts
│   └── tf-apply.sh    # Terraform apply wrapper
│
└── README.md          # This file
```

## 🚀 Quick Start

### Prerequisites

- **Terraform** >= 1.0
- **AWS CLI** configured with appropriate credentials
- **Python** 3.11+ (for Lambda development)

### Deploy to Dev Environment

```bash
# Navigate to dev environment
cd envs/dev

# Initialize Terraform
terraform init

# Review the execution plan
terraform plan

# Apply the configuration
terraform apply

# Get outputs (Lambda URL, etc.)
terraform output
```

### Test the Lambda Function

```bash
# Get the function URL
FUNCTION_URL=$(terraform output -raw lambda_function_url)

# Test health check
curl $FUNCTION_URL

# Test assistant endpoint
curl -X POST $FUNCTION_URL/assistant \
  -H "Content-Type: application/json" \
  -d '{"query": "What properties are available?"}'

# Test properties endpoint
curl $FUNCTION_URL/properties
```

## 📦 Modules

### Lambda Module (`modules/lambda/`)

Creates Lambda functions with IAM roles, CloudWatch logs, and optional Function URLs.

**Key Features:**
- Python 3.11 runtime support
- Configurable memory, timeout, concurrency
- Function URL with CORS
- VPC configuration (optional)
- Environment variables support

**Usage Example:**
```hcl
module "my_lambda" {
  source = "../../modules/lambda"

  function_name = "my-function"
  source_file   = "lambda.zip"
  runtime       = "python3.11"
  memory_size   = 512
  timeout       = 60

  environment_variables = {
    ENV = "production"
  }
}
```

[Full Documentation](modules/lambda/README.md)

### DynamoDB Module (`modules/dynamodb/`)

*Coming soon* - DynamoDB tables for property and tenant data.

### API Module (`modules/api/`)

*Coming soon* - API Gateway configuration.

### Network Module (`modules/network/`)

*Coming soon* - VPC, subnets, and security groups.

### Monitoring Module (`modules/monitoring/`)

*Coming soon* - CloudWatch dashboards and alarms.

## 🌍 Environments

### Development (`envs/dev/`)

- **Purpose**: Development and testing
- **Lambda**: `leasing-assistant-dev`
- **Function URL**: Publicly accessible (no auth)
- **Logging**: DEBUG level, 7-day retention
- **Resources**: Minimal for cost savings

[Dev Environment Documentation](envs/dev/README.md)

### Staging (`envs/staging/`)

*Coming soon* - Pre-production testing environment.

### Production (`envs/prod/`)

*Coming soon* - Production environment with high availability.

## 🛠️ Development Workflow

### Making Changes

1. **Create a branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes to modules or environments**

3. **Test in dev environment**
   ```bash
   cd envs/dev
   terraform plan
   terraform apply
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Add feature X"
   git push origin feature/my-feature
   ```

### Adding a New Lambda Function

1. **Create the Python code** in `envs/{env}/src/`

2. **Configure in Terraform**:
   ```hcl
   data "archive_file" "lambda_zip" {
     type        = "zip"
     source_file = "${path.module}/src/lambda_function.py"
     output_path = "${path.module}/lambda.zip"
   }

   module "my_lambda" {
     source = "../../modules/lambda"
     function_name = "my-function-${var.environment}"
     source_file   = data.archive_file.lambda_zip.output_path
   }
   ```

3. **Deploy**:
   ```bash
   terraform apply
   ```

## 📊 Monitoring & Logs

### View Lambda Logs

```bash
# Using AWS CLI
aws logs tail /aws/lambda/leasing-assistant-dev --follow

# Or use CloudWatch Logs Insights in AWS Console
```

### Monitor Function Performance

```bash
# Get function metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=leasing-assistant-dev \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-01T23:59:59Z \
  --period 3600 \
  --statistics Average,Maximum
```

## 💰 Cost Management

Estimated monthly costs (dev environment):
- **Lambda**: ~$0.20 (with Free Tier)
- **CloudWatch Logs**: ~$0.50
- **DynamoDB**: ~$0 (Free Tier)
- **Total**: < $1/month for dev

For detailed cost breakdown, see [diagrams/cost-breakdown.md](diagrams/cost-breakdown.md).

## 🔒 Security Best Practices

- [ ] Use IAM roles with least privilege
- [ ] Enable CloudWatch logging for all functions
- [ ] Store secrets in AWS Secrets Manager
- [ ] Enable encryption at rest for DynamoDB
- [ ] Use VPC for production workloads
- [ ] Implement API authentication (AWS_IAM or Cognito)
- [ ] Regular security audits with AWS Security Hub

## 🧪 Testing

### Local Testing

```bash
# Test Lambda function locally (requires AWS SAM)
sam local invoke LeasingAssistantFunction -e events/test-event.json
```

### Integration Tests

```bash
# Run integration tests
cd tests
python -m pytest test_lambda.py
```

## 📝 Terraform State Management

### Remote State (Recommended for Teams)

Uncomment the S3 backend configuration in `provider.tf`:

```hcl
backend "s3" {
  bucket         = "leasing-assistant-terraform-state"
  key            = "dev/lambda/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "terraform-state-lock"
}
```

### Create State Resources

```bash
# Create S3 bucket for state
aws s3 mb s3://leasing-assistant-terraform-state --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket leasing-assistant-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

## 🔧 Troubleshooting

### Common Issues

**Issue**: `Error: error configuring Terraform AWS Provider: no valid credential sources`

**Solution**: Configure AWS credentials
```bash
aws configure
# Or use environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"
```

**Issue**: `Error: error creating Lambda function: InvalidParameterValueException`

**Solution**: Check that the ZIP file exists and Python code is valid

**Issue**: Lambda function timing out

**Solution**: Increase timeout in `lambda.tf`:
```hcl
timeout = 120  # Increase from default 60
```

## 🗑️ Cleanup

To destroy all resources in an environment:

```bash
cd envs/dev
terraform destroy
```

⚠️ **Warning**: This will delete all resources. Use with caution!

## 📚 Additional Resources

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Python Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly in dev environment
5. Submit a pull request

## 📄 License

Internal project - All rights reserved

## 📧 Support

For questions or issues, contact the DevOps team or create an issue in the repository.

---

**Last Updated**: November 2025  
**Maintained By**: DevOps Team
