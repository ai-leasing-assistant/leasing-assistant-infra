# Leasing Assistant - Dev Environment

This directory contains the Terraform configuration for deploying the Leasing Assistant Lambda function in the development environment.

## Structure

```
dev/
├── lambda.tf           # Lambda function configuration
├── provider.tf         # Terraform and AWS provider configuration
├── variables.tf        # Input variables
├── outputs.tf          # Output values
├── .gitignore         # Git ignore patterns
├── README.md          # This file
└── src/
    └── lambda_function.py  # Python Lambda function code
```

## Lambda Function

The Lambda function provides the following endpoints:

### Health Check
- **Method**: GET
- **Path**: `/`
- **Description**: Returns service health status

### Assistant Query
- **Method**: POST
- **Path**: `/assistant`
- **Body**:
```json
{
  "query": "Your question here",
  "context": {}
}
```
- **Description**: Process leasing assistant queries

### Get Properties
- **Method**: GET
- **Path**: `/properties`
- **Description**: Retrieve list of available properties

## Deployment

### Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform >= 1.0 installed

### Deploy

```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply the configuration
terraform apply
```

### Testing

After deployment, you can test the Lambda function using the Function URL:

```bash
# Get the function URL from outputs
terraform output lambda_function_url

# Test health check
curl https://your-function-url.lambda-url.us-east-1.on.aws/

# Test assistant endpoint
curl -X POST https://your-function-url.lambda-url.us-east-1.on.aws/assistant \
  -H "Content-Type: application/json" \
  -d '{"query": "What properties are available?"}'

# Test properties endpoint
curl https://your-function-url.lambda-url.us-east-1.on.aws/properties
```

## Configuration

### Variables

- `aws_region`: AWS region (default: us-east-1)

### Environment Variables

The Lambda function uses the following environment variables:
- `ENVIRONMENT`: Environment name (dev)
- `LOG_LEVEL`: Logging level (DEBUG in dev)
- `REGION`: AWS region

## Resources Created

- Lambda Function: `leasing-assistant-dev`
- IAM Role: `leasing-assistant-dev-role`
- CloudWatch Log Group: `/aws/lambda/leasing-assistant-dev`
- Lambda Function URL (publicly accessible)

## Monitoring

View logs in CloudWatch:

```bash
aws logs tail /aws/lambda/leasing-assistant-dev --follow
```

## Cleanup

To remove all resources:

```bash
terraform destroy
```

## Next Steps

1. Integrate with DynamoDB for property storage
2. Add authentication to Function URL
3. Implement actual AI/LLM integration
4. Add API Gateway for advanced routing
5. Set up monitoring and alerting

