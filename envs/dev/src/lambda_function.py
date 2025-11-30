"""
Leasing Assistant Lambda Function
Dev Environment
"""
import json
import os
import logging
from datetime import datetime
from decimal import Decimal
import boto3
import urllib.request
import urllib.error

# Configure logging
logger = logging.getLogger()
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger.setLevel(getattr(logging, log_level))


def lambda_handler(event, context):
    """
    Main Lambda function handler for the Leasing Assistant
    
    Args:
        event: Lambda event object containing request data
        context: Lambda context object with runtime information
        
    Returns:
        dict: Response object with statusCode, headers, and body
    """
    logger.info("Lambda function invoked")
    logger.debug(f"Event: {json.dumps(event, default=str)}")
    
    # Get environment variables
    environment = os.environ.get('ENVIRONMENT', 'unknown')
    region = os.environ.get('REGION', 'unknown')
    
    try:
        # Parse the event
        http_method = event.get('requestContext', {}).get('http', {}).get('method', 'UNKNOWN')
        path = event.get('rawPath', '/')
        
        # Parse body if present
        body = {}
        if event.get('body'):
            try:
                body = json.loads(event['body'])
            except json.JSONDecodeError:
                body = {'raw': event['body']}
        
        logger.info(f"Processing {http_method} request to {path}")
        
        # Route the request
        if http_method == 'GET' and path == '/':
            response = handle_health_check(context, environment, region)
        elif http_method == 'POST' and path == '/assistant':
            response = handle_assistant_request(body, context)
        elif http_method == 'GET' and path == '/property':
            response = handle_property_request(event, context)
        elif http_method == 'GET' and path == '/properties':
            response = handle_get_properties(context)
        else:
            response = {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Not Found',
                    'message': f'No handler for {http_method} {path}'
                })
            }
        
        logger.info("Request processed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal Server Error',
                'message': str(e),
                'environment': environment
            })
        }


def handle_health_check(context, environment, region):
    """
    Handle health check requests
    
    Returns:
        dict: Health check response
    """
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'status': 'healthy',
            'service': 'leasing-assistant',
            'environment': environment,
            'region': region,
            'function_name': context.function_name,
            'function_version': context.function_version,
            'timestamp': datetime.utcnow().isoformat(),
            'message': 'Leasing Assistant Lambda is running'
        })
    }


def handle_assistant_request(body, context):
    """
    Handle leasing assistant requests
    
    Args:
        body: Request body containing the assistant query
        context: Lambda context
        
    Returns:
        dict: Assistant response
    """
    user_query = body.get('query', '')
    user_context = body.get('context', {})
    
    logger.info(f"Processing assistant query: {user_query}")
    
    # TODO: Implement actual AI/assistant logic here
    # This is a placeholder response
    response_data = {
        'query': user_query,
        'response': f"Echo: {user_query}",
        'timestamp': datetime.utcnow().isoformat(),
        'request_id': context.request_id,
        'suggestions': [
            'Would you like to see available properties?',
            'Do you need help with lease terms?',
            'Can I help you schedule a viewing?'
        ],
        'metadata': {
            'processed_by': context.function_name,
            'context': user_context
        }
    }
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(response_data)
    }

def handle_property_request(event, context):
    """
    Handle GET /property?id=landlord_id:property_id
    - Fetch record from DynamoDB using the composite id as partition key
    - Call OpenAI with the record context
    - Return and log the OpenAI response
    """
    table_name = os.environ.get('DDB_TABLE_NAME')
    if not table_name:
        return _error_response(
            500,
            "DDB_TABLE_NAME environment variable is not set. Please configure the Lambda environment."
        )

    query_params = event.get('queryStringParameters') or {}
    composite_id = query_params.get('id')
    if not composite_id:
        return _error_response(400, "Missing required query parameter 'id' formatted as 'landlord_id:property_id'.")

    logger.info(f"Fetching property by id: {composite_id} from table: {table_name}")
    item = _get_item_from_dynamodb(table_name, {"property_id": composite_id})

    if not item:
        return _error_response(404, f"No record found for id '{composite_id}'.")

    # Prepare prompt from item
    prompt = _build_property_prompt(item)

    # Call OpenAI
    try:
        ai_response = _call_openai_chat(prompt)
    except Exception as e:
        logger.error(f"OpenAI call failed: {str(e)}", exc_info=True)
        return _error_response(502, f"Failed to get response from OpenAI: {str(e)}")

    # Print AI response to logs and return
    print(ai_response)  # Also visible in CloudWatch logs
    logger.info(f"OpenAI response: {ai_response}")

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'id': composite_id,
            'openai_response': ai_response,
            'timestamp': datetime.utcnow().isoformat()
        })
    }


def handle_get_properties(context):
    """
    Handle requests to get properties list
    
    Args:
        context: Lambda context
        
    Returns:
        dict: Properties list response
    """
    logger.info("Fetching properties list")
    
    # TODO: Implement actual database query here
    # This is mock data
    properties = [
        {
            'id': '1',
            'name': 'Luxury Downtown Apartment',
            'address': '123 Main St',
            'bedrooms': 2,
            'bathrooms': 2,
            'rent': 2500,
            'available': True
        },
        {
            'id': '2',
            'name': 'Cozy Studio',
            'address': '456 Oak Ave',
            'bedrooms': 0,
            'bathrooms': 1,
            'rent': 1200,
            'available': True
        },
        {
            'id': '3',
            'name': 'Family House',
            'address': '789 Elm Street',
            'bedrooms': 4,
            'bathrooms': 3,
            'rent': 3800,
            'available': False
        }
    ]
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'properties': properties,
            'count': len(properties),
            'timestamp': datetime.utcnow().isoformat()
        })
    }


# -------- Helpers --------

def _error_response(status, message):
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'error': message})
    }


def _get_item_from_dynamodb(table_name, key):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    resp = table.get_item(Key=key)
    item = resp.get('Item')
    if not item:
        return None
    # Convert Decimals for safe JSON/use
    return _convert_decimals(item)


def _convert_decimals(obj):
    if isinstance(obj, list):
        return [_convert_decimals(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        # Prefer int if no fractional part
        if obj % 1 == 0:
            return int(obj)
        return float(obj)
    return obj


def _build_property_prompt(item):
    # Create a concise prompt with key property attributes
    summary = json.dumps(item)  # already decimal-converted
    return (
        "You are a helpful leasing assistant. Analyze the following property record "
        "and provide a concise, friendly summary highlighting the most important details "
        "for a prospective tenant. Include location, size, notable amenities, pricing, "
        "and unique selling points. If any useful information is missing, state the "
        "top 2-3 follow-up questions.\n\n"
        f"Property JSON:\n{summary}"
    )


def _call_openai_chat(prompt):
    """
    Calls OpenAI Chat Completions API using standard library (urllib) to avoid external deps.
    Requires OPENAI_API_KEY env variable. Optional OPENAI_MODEL (default gpt-4o-mini).
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

    model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a leasing assistant for rental properties."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_body = resp.read()
            parsed = json.loads(resp_body.decode("utf-8"))
            content = (
                parsed.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            if not content:
                raise RuntimeError("Empty response from OpenAI.")
            return content
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if hasattr(e, "read") else str(e)
        raise RuntimeError(f"HTTP {e.code}: {err_body}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {str(e)}")

