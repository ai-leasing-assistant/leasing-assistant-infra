# Lambda Function for Dev Environment

# Create Lambda deployment package from source
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/src/lambda_function.py"
  output_path = "${path.module}/lambda.zip"
}

# Deploy Lambda function using the module
module "leasing_assistant_lambda" {
  source = "../../modules/lambda"

  function_name = "leasing-assistant-dev"
  description   = "Leasing Assistant Lambda function for dev environment"
  source_file   = data.archive_file.lambda_zip.output_path
  runtime       = "python3.11"
  handler       = "lambda_function.lambda_handler"
  timeout       = 60
  memory_size   = 512

  environment_variables = {
    ENVIRONMENT = "dev"
    LOG_LEVEL   = "DEBUG"
    REGION      = var.aws_region
  }

  log_retention_days = 7

  # Enable Function URL for easy testing in dev
  enable_function_url    = true
  function_url_auth_type = "NONE"

  function_url_cors = {
    allow_credentials = false
    allow_origins     = ["*"]
    allow_methods     = ["GET", "POST", "PUT", "DELETE"]
    allow_headers     = ["Content-Type", "Authorization"]
    expose_headers    = []
    max_age           = 300
  }

  tags = {
    Environment = "dev"
    Project     = "leasing-assistant"
    ManagedBy   = "terraform"
  }
}

