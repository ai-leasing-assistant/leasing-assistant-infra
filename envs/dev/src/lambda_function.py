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
        elif http_method == 'POST' and (path == '/property' or path.endswith('/property')):
            response = handle_property_webhook(event, context)
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


def _build_property_prompt(aistate, property_item, body_text):
    """
    Create a prompt combining aiState, property details, and body text.
    """
    prop_json = json.dumps(property_item)  # already decimal-converted
    header = (
        "You are a friendly, professional AI Leasing Assistant that represents the landlord and helps prospective tenants learn about a rental property."
        ""
        "Your goals are:"
        "1. Answer questions naturally using the property details provided."
        "2. Maintain continuity using the session context without repeating it back verbatim."
        "3. Ask smart follow-up questions when information is missing or unclear."
        "4. Qualify the lead politely (income, move-in date, pets, occupancy count, credit issues, etc.)."
        "5. Move the conversation forward in a warm, conversational tone."
        "6. Guide the lead toward scheduling an in-person or virtual tour when they seem like a good match."
        "7. Keep responses clear, concise, positive, and human-like."
        ""
        "Guidelines:"
        "- Never invent details not found in the property data."
        "- If the lead asks for unavailable information, say you will confirm with the landlord."
        "- If the lead seems unqualified based on the requirements, respond politely but firmly."
        "- Always try to keep the conversation flowing with one helpful follow-up question or next step."
        "- When appropriate, offer specific showing time options instead of asking open-ended questions."
        ""
        "You must always prioritize helping the lead progress toward a showing if they appear interested."
    )
    parts = [header, "Property JSON:\n", prop_json]
    return "".join(parts)


def handle_property_webhook(event, context):
    """
    Handle Twilio webhook POST to /property.
    - Content-Type: application/x-www-form-urlencoded
    - Must check if there is a session for the incoming number.
    Convention:
      - Session item keyed by PK='LEAD#+<From>', SK='CONTEXT' (adjust if your schema differs).
    Response: JSON indicating whether a session exists and basic echo of inbound fields.
    """
    sessions_table = os.environ.get('TENANT_SESSIONS_TABLE_NAME', 'TenantSessions')
    leasing_app = os.environ.get('LEASING_APP_TABLE_NAME', 'LeasingApp')
    form = _parse_form_urlencoded(event)

    from_number = form.get('From') or form.get('from') or ''
    to_number = form.get('To') or form.get('to') or ''
    body_text = form.get('Body') or form.get('body') or ''
    message_sid = form.get('MessageSid') or form.get('messagesid') or ''

    if not from_number:
        return _error_response(400, "Missing 'From' in webhook body.")

    # Session schema per your example:
    #   PK = "LEAD#+<phone>"
    #   SK = "CONTEXT"
    pk = f"LEAD#{from_number}"
    sk = "CONTEXT"
    logger.info(f"Checking if session exists for number {from_number} in table {sessions_table} (PK={pk}, SK={sk})")

    session_item = _get_item_from_dynamodb(sessions_table, {"PK": pk, "SK": sk})
    exists = session_item is not None

    if exists:
        # get aiState from session item
        aistate = session_item.get('aiState')

        # get landlordId and propertyId#unitId from session item
        landlordId = session_item.get('landlordId')
        propertyId = session_item.get('propertyId')
        unitId = session_item.get('unitId')

        # get property details from leasing app table in json format using landlordId and propertyId#unitId
        property_item = _get_item_from_dynamodb(leasing_app, {"PK": landlordId, "SK": f"UNIT#{propertyId}#{unitId}"})
        property_json = json.dumps(property_item)

        # call openai chat with aistate, property details, and body_text
        prompt = _build_property_prompt(aistate, property_json, body_text)
        response = _call_openai_chat(prompt)
        # update session item with new aiState
        session_item['aiState'] = response
        #_update_item_in_dynamodb(sessions_table, session_item)
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'response': response})
        }
    else:   
        return _error_response(404, "No session found for number {from_number}")

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

