# leasing-assistant-infra
Infrastructure-as-code for deploying the entire AI Leasing Assistant platform using Terraform. Manages networking, compute, DynamoDB, ECS/EKS, monitoring, secrets, and CI/CD pipelines across dev, staging, and production environments.

# Lambda Function Terraform Module

This module creates an AWS Lambda function with Python runtime, including IAM role, CloudWatch logs, and optional features like VPC configuration and Function URLs.

## Features

- Lambda function with Python runtime
- IAM role with basic execution permissions
- CloudWatch Logs integration with configurable retention
- Optional VPC configuration
- Optional Lambda Function URL with CORS support
- Configurable memory, timeout, and concurrency settings
- Support for environment variables

## Usage

### Basic Example

```hcl
module "lambda" {
  source = "../../modules/lambda"

  function_name = "my-python-function"
  description   = "My basic Python Lambda function"
  source_file   = "lambda.zip"
  runtime       = "python3.11"
  handler       = "lambda_function.lambda_handler"
  timeout       = 30
  memory_size   = 256

  tags = {
    Environment = "dev"
    Project     = "leasing-assistant"
  }
}
```

### Example with Environment Variables

```hcl
module "lambda" {
  source = "../../modules/lambda"

  function_name = "my-python-function"
  source_file   = "lambda.zip"
  
  environment_variables = {
    ENV       = "production"
    LOG_LEVEL = "INFO"
    API_KEY   = var.api_key
  }
}
```

### Example with VPC Configuration

```hcl
module "lambda" {
  source = "../../modules/lambda"

  function_name = "my-vpc-function"
  source_file   = "lambda.zip"
  
  vpc_config = {
    subnet_ids         = ["subnet-12345", "subnet-67890"]
    security_group_ids = ["sg-12345"]
  }
}
```

### Example with Function URL

```hcl
module "lambda" {
  source = "../../modules/lambda"

  function_name          = "my-web-function"
  source_file            = "lambda.zip"
  enable_function_url    = true
  function_url_auth_type = "NONE"
  
  function_url_cors = {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["GET", "POST"]
    allow_headers     = ["Content-Type"]
    expose_headers    = []
    max_age           = 300
  }
}
```

### Example with Archive File Data Source

```hcl
# Create Lambda deployment package
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/src/lambda_function.py"
  output_path = "${path.module}/lambda.zip"
}

module "lambda" {
  source = "../../modules/lambda"

  function_name = "my-python-function"
  source_file   = data.archive_file.lambda_zip.output_path
  runtime       = "python3.11"
}
```

## Creating the Lambda Deployment Package

### Simple Python Function

Create a Python file:

```python
# lambda_function.py
import json

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
```

Package it:

```bash
zip lambda.zip lambda_function.py
```

### With Dependencies

If you have dependencies, install them first:

```bash
pip install -r requirements.txt -t ./package
cd package
zip -r ../lambda.zip .
cd ..
zip -g lambda.zip lambda_function.py
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| function_name | Name of the Lambda function | string | - | yes |
| source_file | Path to the Lambda deployment package (ZIP file) | string | - | yes |
| description | Description of the Lambda function | string | "" | no |
| handler | Lambda function handler | string | "lambda_function.lambda_handler" | no |
| runtime | Lambda runtime | string | "python3.11" | no |
| timeout | Function timeout in seconds | number | 30 | no |
| memory_size | Function memory size in MB | number | 128 | no |
| environment_variables | Environment variables for the function | map(string) | null | no |
| vpc_config | VPC configuration | object | null | no |
| reserved_concurrent_executions | Reserved concurrent executions | number | -1 | no |
| log_retention_days | CloudWatch log retention period in days | number | 7 | no |
| enable_function_url | Enable Lambda function URL | bool | false | no |
| function_url_auth_type | Authorization type for function URL | string | "NONE" | no |
| function_url_cors | CORS configuration for function URL | object | null | no |
| tags | Tags to apply to all resources | map(string) | {} | no |

## Outputs

| Name | Description |
|------|-------------|
| function_name | Name of the Lambda function |
| function_arn | ARN of the Lambda function |
| function_invoke_arn | Invoke ARN of the Lambda function |
| function_version | Latest published version |
| function_qualified_arn | Qualified ARN of the Lambda function |
| role_arn | ARN of the Lambda IAM role |
| role_name | Name of the Lambda IAM role |
| log_group_name | Name of the CloudWatch log group |
| log_group_arn | ARN of the CloudWatch log group |
| function_url | URL of the Lambda function (if enabled) |

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0 |
| aws | >= 4.0 |

## Python Runtime Versions

Supported Python runtimes:
- python3.11 (recommended)
- python3.10
- python3.9
- python3.8

## Notes

- The module automatically creates a CloudWatch Log Group with configurable retention
- IAM role includes basic Lambda execution permissions
- If VPC configuration is provided, VPC execution permissions are automatically added
- Function URL is optional and disabled by default
- Source code hash is automatically calculated for deployment updates