resource "aws_dynamodb_table" "leasing_app" {
  name         = "LeasingApp"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "PK"
  range_key = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  attribute {
    name = "GSI1PK"
    type = "S"
  }

  attribute {
    name = "GSI1SK"
    type = "S"
  }

  global_secondary_index {
    name            = "GSI1"
    hash_key        = "GSI1PK"
    range_key       = "GSI1SK"
    projection_type = "ALL"
  }
}

resource "aws_dynamodb_table" "tenant_sessions" {
  name         = "TenantSessions"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "PK"
  range_key = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }
}

# Add sample data to the leasing app table
resource "aws_dynamodb_table_item" "landlord_sample_data" {
  table_name = aws_dynamodb_table.leasing_app.name
  hash_key   = aws_dynamodb_table.leasing_app.hash_key
  range_key  = aws_dynamodb_table.leasing_app.range_key

  item = jsonencode({
    PK = {
      S = "LANDLORD#123"
    }
    SK = {
      S = "UNIT#456#APT1A"
    }
    smsAppHash = {
      S = "#906nassau"
    }
    GSI1PK = {
      S = "#906nassau"
    }
    GSI1SK = {
      S = "LANDLORD#123#UNIT#456#APT1A"
    }
    amenities = {
      L = [
        { S = "On-site fitness center" },
        { S = "Secure entry" },
        { S = "Outdoor courtyard" }
      ]
    }
    applicationFee = {
      N = "45"
    }
    available = {
      BOOL = true
    }
    availableDate = {
      S = "2025-12-01"
    }
    bathrooms = {
      N = "1"
    }
    bedrooms = {
      N = "2"
    }
    description = {
      S = "Spacious 2-bedroom, 1-bath unit with modern finishes, updated kitchen, large closets, and plenty of natural light. Located near downtown shopping and public transit. Perfect for small families or young professionals."
    }
    floorLevel = {
      S = "1st floor"
    }
    heatingCooling = {
      S = "Central HVAC"
    }
    laundry = {
      S = "In-unit washer/dryer"
    }
    leaseLength = {
      S = "12 months minimum"
    }
    parking = {
      S = "1 assigned spot included"
    }
    petPolicy = {
      S = "Cats allowed. No dogs."
    }
    propertyId = {
      S = "456"
    }
    rent = {
      N = "1450"
    }
    securityDeposit = {
      N = "1450"
    }
    squareFeet = {
      N = "850"
    }
    tourOptions = {
      S = "In-person showings available Mon–Fri, 10 AM–6 PM"
    }
    unitId = {
      S = "APT1A"
    }
    utilitiesIncluded = {
      S = "Water, trash"
    }
  })

  lifecycle {
    ignore_changes = [item]
  }
}
