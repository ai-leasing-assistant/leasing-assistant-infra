# DynamoDB Table Resource

resource "aws_dynamodb_table" "this" {
  name         = var.table_name
  billing_mode = var.billing_mode

  # Capacity only when PROVISIONED
  read_capacity  = var.billing_mode == "PROVISIONED" ? coalesce(var.read_capacity, 1) : null
  write_capacity = var.billing_mode == "PROVISIONED" ? coalesce(var.write_capacity, 1) : null

  hash_key  = var.partition_key_name
  range_key = var.sort_key_name != null ? var.sort_key_name : null

  attribute {
    name = var.partition_key_name
    type = var.partition_key_type
  }

  dynamic "attribute" {
    for_each = var.sort_key_name != null ? [1] : []
    content {
      name = var.sort_key_name
      type = var.sort_key_type
    }
  }

  # Stream settings
  stream_enabled   = var.stream_enabled
  stream_view_type = var.stream_enabled ? var.stream_view_type : null

  # Server-side encryption (AWS owned CMK by default)
  server_side_encryption {
    enabled = var.sse_enabled
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = var.pitr_enabled
  }

  tags = merge(
    var.tags,
    {
      Name = var.table_name
    }
  )
}


