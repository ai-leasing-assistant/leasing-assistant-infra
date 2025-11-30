# SSM SecureString Parameter Variables

variable "name" {
  description = "Name of the SSM parameter (e.g., /leasing-assistant/dev/openai_api_key)"
  type        = string
}

variable "value" {
  description = "Secret value to store in the SSM parameter"
  type        = string
  sensitive   = true
}

variable "description" {
  description = "Description for the SSM parameter"
  type        = string
  default     = ""
}

variable "key_id" {
  description = "KMS Key ID or ARN to encrypt the SecureString (optional; AWS managed key used if null)"
  type        = string
  default     = null
}

variable "overwrite" {
  description = "Allow overwriting an existing parameter of the same name"
  type        = bool
  default     = true
}

variable "tier" {
  description = "Parameter tier (Standard, Advanced, Intelligent-Tiering)"
  type        = string
  default     = "Standard"
}

variable "tags" {
  description = "Tags to apply to the SSM parameter"
  type        = map(string)
  default     = {}
}


