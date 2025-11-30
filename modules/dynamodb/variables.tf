# DynamoDB Table Variables

variable "table_name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "partition_key_name" {
  description = "Partition (hash) key attribute name"
  type        = string
  default     = "property_id"
}

variable "partition_key_type" {
  description = "Partition (hash) key attribute type (S, N, or B)"
  type        = string
  default     = "S"
}

variable "sort_key_name" {
  description = "Sort (range) key attribute name (optional)"
  type        = string
  default     = null
}

variable "sort_key_type" {
  description = "Sort (range) key attribute type (S, N, or B)"
  type        = string
  default     = "S"
}

variable "billing_mode" {
  description = "Billing mode for the table (PAY_PER_REQUEST or PROVISIONED)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "read_capacity" {
  description = "Read capacity units (only when billing_mode is PROVISIONED)"
  type        = number
  default     = null
}

variable "write_capacity" {
  description = "Write capacity units (only when billing_mode is PROVISIONED)"
  type        = number
  default     = null
}

variable "pitr_enabled" {
  description = "Enable Point-in-time recovery (PITR)"
  type        = bool
  default     = true
}

variable "sse_enabled" {
  description = "Enable server-side encryption (SSE) with AWS owned CMK"
  type        = bool
  default     = true
}

variable "stream_enabled" {
  description = "Enable DynamoDB streams"
  type        = bool
  default     = false
}

variable "stream_view_type" {
  description = "When streams enabled, the view type (NEW_IMAGE, OLD_IMAGE, NEW_AND_OLD_IMAGES, KEYS_ONLY)"
  type        = string
  default     = "NEW_AND_OLD_IMAGES"
}

variable "tags" {
  description = "Tags to apply to the DynamoDB table"
  type        = map(string)
  default     = {}
}


