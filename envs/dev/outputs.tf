# Lambda Outputs

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = module.leasing_assistant_lambda.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = module.leasing_assistant_lambda.function_arn
}

output "lambda_function_url" {
  description = "URL endpoint for the Lambda function"
  value       = module.leasing_assistant_lambda.function_url
}

output "lambda_role_arn" {
  description = "ARN of the Lambda IAM role"
  value       = module.leasing_assistant_lambda.role_arn
}

output "lambda_log_group_name" {
  description = "CloudWatch log group name"
  value       = module.leasing_assistant_lambda.log_group_name
}

