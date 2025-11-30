resource "aws_ssm_parameter" "secret" {
  name        = var.name
  description = var.description
  type        = "SecureString"
  value       = var.value
  key_id      = var.key_id != null ? var.key_id : null
  overwrite   = var.overwrite
  tier        = var.tier

  tags = merge(
    var.tags,
    {
      Name = var.name
    }
  )
}


