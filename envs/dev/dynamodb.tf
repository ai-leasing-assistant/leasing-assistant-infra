# DynamoDB Table for Dev Environment

module "property_table" {
  source = "../../modules/dynamodb"

  table_name          = "leasing-assistant-properties-dev"
  partition_key_name  = "landlord_id:property_id"
  partition_key_type  = "S"

  # Defaults: PAY_PER_REQUEST billing, SSE enabled, PITR enabled, streams disabled.
}


