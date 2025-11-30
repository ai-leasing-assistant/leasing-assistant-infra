output "parameter_name" {
  description = "Name of the SSM parameter"
  value       = aws_ssm_parameter.secret.name
}

output "parameter_arn" {
  description = "ARN of the SSM parameter"
  value       = aws_ssm_parameter.secret.arn
}

output "parameter_version" {
  description = "Version of the SSM parameter"
  value       = aws_ssm_parameter.secret.version
}


