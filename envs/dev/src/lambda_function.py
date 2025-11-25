"""
Leasing Assistant Lambda Function
Dev Environment
"""
import json
import os
import logging
from datetime import datetime

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

