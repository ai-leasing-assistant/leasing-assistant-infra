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
import re

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
        path_raw = event.get('rawPath', '/')
        # Normalize multiple slashes (e.g., //property -> /property)
        path = re.sub(r'/+', '/', path_raw or '/')
        
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
        elif http_method == 'POST' and (path == '/sms' or path.endswith('/sms')):
            response = handle_echo_sms(event, context)
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

def _query_dynamodb_by_gsi1pk(table_name, gsi1pk):
    """
    Query DynamoDB table using GSI1 where GSI1PK matches the provided value.
    Returns a list of items (empty list if none found).
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    resp = table.query(
        IndexName='GSI1',
        KeyConditionExpression='GSI1PK = :gsi1pk',
        ExpressionAttributeValues={':gsi1pk': gsi1pk}
    )
    items = resp.get('Items', [])
    # Convert Decimals for safe JSON/use
    return [_convert_decimals(item) for item in items]

def _update_item_in_dynamodb(table_name, key, update_expression, expression_attribute_values):
    """
    Update an item in DynamoDB using update expression.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    table.update_item(
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values
    )

def _put_item_in_dynamodb(table_name, item):
    """
    Put (create or replace) an item in DynamoDB.
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    table.put_item(Item=item)

def _parse_pk_sk_from_query(qs, id_key, pk_key, sk_key):
    """
    Returns (pk, sk) from either id=PK:SK or pk=&sk=; returns (None, None) if not provided/invalid.
    """
    composite = qs.get(id_key)
    if composite:
        parts = composite.split(':', 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return None, None
    pk = qs.get(pk_key)
    sk = qs.get(sk_key)
    if pk and sk:
        return pk, sk
    return None, None

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


def _build_property_messages(aistate, property_item, body_text):
    """
    Create a messages array for OpenAI chat API combining aiState (previous conversation),
    property details, and current user message (body_text).
    
    Returns:
        list: Array of message dicts with 'role' and 'content' keys
    """
    prop_json = json.dumps(property_item)  # already decimal-converted
    system_content = (
        "You are a friendly, professional AI Leasing Assistant that represents the landlord "
        "and helps prospective tenants learn about a rental property.\n\n"
        "Your goals are:\n"
        "1. Answer questions naturally using the property details provided.\n"
        "2. Maintain continuity using the session context without repeating it back verbatim.\n"
        "3. Ask smart follow-up questions when information is missing or unclear.\n"
        "4. Qualify the lead politely (income, move-in date, pets, occupancy count, credit issues, etc.).\n"
        "5. Move the conversation forward in a warm, conversational tone.\n"
        "6. Guide the lead toward scheduling an in-person or virtual tour when they seem like a good match.\n"
        "7. Keep responses clear, concise, positive, and human-like.\n\n"
        "Guidelines:\n"
        "- Never invent details not found in the property data.\n"
        "- If the lead asks for unavailable information, say you will confirm with the landlord.\n"
        "- If the lead seems unqualified based on the requirements, respond politely but firmly.\n"
        "- Always try to keep the conversation flowing with one helpful follow-up question or next step.\n"
        "- When appropriate, offer specific showing time options instead of asking open-ended questions.\n\n"
        "You must always prioritize helping the lead progress toward a showing if they appear interested.\n\n"
        f"Property JSON:\n{prop_json}"
    )
    
    messages = [
        {"role": "system", "content": system_content}
    ]
    
    # If there's previous conversation state (aistate), add it as assistant's previous response
    if aistate:
        messages.append({
            "role": "assistant",
            "content": aistate
        })
    
    # Add the current user message
    messages.append({
        "role": "user",
        "content": body_text
    })
    
    return messages

def handle_echo_sms(event, context):
    """
    POST /sms
    Accepts application/x-www-form-urlencoded payload.
    Uses the Body text to search DynamoDB for items matching smsAppHash (via GSI1PK).
    Calls OpenAI with the property details and returns the AI response.
    Manages tenant session state in DynamoDB.
    """
    sessions_table = os.environ.get('TENANT_SESSIONS_TABLE_NAME', 'TenantSessions')
    leasing_app = os.environ.get('LEASING_APP_TABLE_NAME', 'LeasingApp')
    form = _parse_form_urlencoded(event)
    from_number = form.get('From') or form.get('from') or ''
    body_text = form.get('Body') or form.get('body') or ''

    logger.info(f"SMS received - From: {from_number}, Body: {body_text}")

    if not from_number:
        return _error_response(400, "Missing 'From' in SMS payload.")
    
    if not body_text:
        return _error_response(400, "Missing 'Body' in SMS payload.")

    # Check if there is an active session for this phone number
    pk = f"LEAD#{from_number}"
    sk = "CONTEXT"
    logger.info(f"Checking if session exists for number {from_number} in table {sessions_table} (PK={pk}, SK={sk})")
    
    session_item = _get_item_from_dynamodb(sessions_table, {"PK": pk, "SK": sk})
    
    # Determine smsAppHash: use from session if exists, otherwise extract from body text
    if session_item and session_item.get('smsAppHash'):
        # Active session exists - use smsAppHash from session
        sms_app_hash = session_item.get('smsAppHash')
        logger.info(f"Using smsAppHash from active session: {sms_app_hash}")
    else:
        # No active session - extract hash from body text
        if body_text.strip().startswith('#'):
            sms_app_hash = body_text.strip()
            # Normalize to ensure it starts with #
            if not sms_app_hash.startswith('#'):
                sms_app_hash = f"#{sms_app_hash}"
            logger.info(f"Extracting smsAppHash from body text: {sms_app_hash}")
        else:
            return _error_response(404, "No active session found and no hash provided in message. Please start with a property hash (e.g., #906nassau).")

    # Query the property item from the leasing app table using GSI1
    logger.info(f"Querying property with smsAppHash: {sms_app_hash} in table {leasing_app}")
    matching_items = _query_dynamodb_by_gsi1pk(leasing_app, sms_app_hash)
    
    if not matching_items:
        return _error_response(404, f"No property found for hash: {sms_app_hash}")

    # Use the first matching property item
    property_item = matching_items[0]
    logger.info(f"Found property: PK={property_item.get('PK')}, SK={property_item.get('SK')}")

    # Extract property details
    landlord_id = property_item.get('PK')  # e.g., "LANDLORD#123"
    property_id = property_item.get('propertyId')
    unit_id = property_item.get('unitId')
    # Ensure we use the smsAppHash from the property item (in case it differs slightly)
    property_sms_app_hash = property_item.get('smsAppHash', sms_app_hash)
    
    # Get existing aiState if session exists, otherwise None for first message
    aistate = session_item.get('aiState') if session_item else None
    
    # Build messages array with property details, previous conversation (aistate), and current user message
    messages = _build_property_messages(aistate, property_item, body_text)
    
    # Call OpenAI with the messages
    try:
        ai_response = _call_openai_chat(messages)
        logger.info("OpenAI response generated successfully")
    except Exception as e:
        logger.error(f"Error calling OpenAI: {str(e)}", exc_info=True)
        return _error_response(500, f"Error generating AI response: {str(e)}")

    # Update or create session with new aiState and smsAppHash
    if session_item:
        # Update existing session
        logger.info(f"Updating existing session for {from_number}")
        _update_item_in_dynamodb(
            sessions_table,
            {"PK": pk, "SK": sk},
            "SET aiState = :aistate, lastMessage = :lastMessage, lastUpdated = :lastUpdated, smsAppHash = :smsAppHash",
            {
                ':aistate': ai_response,
                ':lastMessage': body_text,
                ':lastUpdated': datetime.utcnow().isoformat(),
                ':smsAppHash': property_sms_app_hash
            }
        )
    else:
        # Create new session
        logger.info(f"Creating new session for {from_number}")
        new_session = {
            'PK': pk,
            'SK': sk,
            'aiState': ai_response,
            'landlordId': landlord_id,
            'propertyId': property_id,
            'unitId': unit_id,
            'leadPhone': from_number,
            'lastMessage': body_text,
            'lastUpdated': datetime.utcnow().isoformat(),
            'smsAppHash': property_sms_app_hash
        }
        _put_item_in_dynamodb(sessions_table, new_session)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'from': from_number,
            'body': body_text,
            'searchHash': property_sms_app_hash,
            'property': {
                'PK': property_item.get('PK'),
                'SK': property_item.get('SK'),
                'propertyId': property_item.get('propertyId'),
                'unitId': property_item.get('unitId')
            },
            'response': ai_response,
            'timestamp': datetime.utcnow().isoformat()
        })
    }

def _parse_form_urlencoded(event):
    """
    Parse application/x-www-form-urlencoded body from API Gateway (v2). Handles base64.
    Returns a flat dict of first values.
    """
    try:
        import base64
        from urllib.parse import parse_qs
    except Exception:
        return {}

    body = event.get('body')
    if body is None:
        return {}
    if event.get('isBase64Encoded'):
        try:
            body = base64.b64decode(body).decode('utf-8')
        except Exception:
            return {}
    # parse_qs returns dict[str, list[str]]
    parsed = parse_qs(body, keep_blank_values=True)
    # Flatten to first value
    flat = {k: v[0] if isinstance(v, list) and v else '' for k, v in parsed.items()}
    return flat


def _call_openai_chat(messages):
    """
    Calls OpenAI Chat Completions API using standard library (urllib) to avoid external deps.
    Requires OPENAI_API_KEY env variable. Optional OPENAI_MODEL (default gpt-4o-mini).
    
    Args:
        messages: List of message dicts with 'role' and 'content' keys (e.g., 
                  [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}])
    
    Returns:
        str: The assistant's response content
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

    model = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
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

