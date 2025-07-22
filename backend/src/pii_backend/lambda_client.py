"""
AWS Lambda Client for PII Operations
"""

import json
import asyncio
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError
import logging

from .config import settings

logger = logging.getLogger(__name__)


class LambdaClient:
    """AWS Lambda client for PII encryption operations"""
    
    def __init__(self):
        """Initialize Lambda client"""
        self.lambda_client = boto3.client(
            'lambda',
            region_name=settings.aws_region
        )
        self.function_name = settings.lambda_function_name
        self.timeout = settings.lambda_timeout
        self.retry_attempts = settings.lambda_retry_attempts
    
    async def _invoke_lambda(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke Lambda function with retry logic"""
        
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Invoking Lambda function: {self.function_name}")
                logger.debug(f"Payload: {json.dumps(payload, default=str)}")
                
                # Run boto3 call in thread pool to make it async
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.lambda_client.invoke(
                        FunctionName=self.function_name,
                        InvocationType='RequestResponse',
                        Payload=json.dumps(payload, default=str)
                    )
                )
                
                # Parse response
                response_payload = response['Payload'].read()
                result = json.loads(response_payload)
                
                logger.info(f"Lambda response status: {result.get('statusCode')}")
                logger.debug(f"Lambda response: {result}")
                
                return result
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                
                logger.error(f"Lambda invocation failed (attempt {attempt + 1}): {error_code} - {error_message}")
                
                if attempt == self.retry_attempts - 1:
                    raise Exception(f"Lambda invocation failed after {self.retry_attempts} attempts: {error_message}")
                
                # Wait before retry (exponential backoff)
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error(f"Unexpected error invoking Lambda (attempt {attempt + 1}): {str(e)}")
                
                if attempt == self.retry_attempts - 1:
                    raise Exception(f"Lambda invocation failed: {str(e)}")
                
                # Wait before retry
                await asyncio.sleep(2 ** attempt)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Lambda function health"""
        payload = {
            "operation": "health"
        }
        
        result = await self._invoke_lambda(payload)
        
        # Parse the body if it's a string
        if isinstance(result.get('body'), str):
            try:
                body = json.loads(result['body'])
                result.update(body)
            except json.JSONDecodeError:
                pass
        
        return result
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user with PII encryption"""
        payload = {
            "operation": "create_user",
            "data": user_data
        }
        
        result = await self._invoke_lambda(payload)
        
        # Parse the body if it's a string  
        if isinstance(result.get('body'), str):
            try:
                body = json.loads(result['body'])
                result.update(body)
            except json.JSONDecodeError:
                pass
        
        return result
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID with PII decryption"""
        payload = {
            "operation": "get_user",
            "user_id": user_id
        }
        
        result = await self._invoke_lambda(payload)
        
        # Parse the body if it's a string
        if isinstance(result.get('body'), str):
            try:
                body = json.loads(result['body'])
                result.update(body)
            except json.JSONDecodeError:
                pass
        
        return result
    
    async def list_users(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """List users with basic information"""
        payload = {
            "operation": "list_users",
            "limit": limit,
            "offset": offset
        }
        
        result = await self._invoke_lambda(payload)
        
        # Parse the body if it's a string
        if isinstance(result.get('body'), str):
            try:
                body = json.loads(result['body'])
                result.update(body)
            except json.JSONDecodeError:
                pass
        
        return result
    
    async def get_audit_trail(
        self, 
        user_id: Optional[str] = None, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get audit trail for user or all users"""
        payload = {
            "operation": "audit_trail",
            "limit": limit
        }
        
        if user_id:
            payload["user_id"] = user_id
        
        result = await self._invoke_lambda(payload)
        
        # Parse the body if it's a string
        if isinstance(result.get('body'), str):
            try:
                body = json.loads(result['body'])
                result.update(body)
            except json.JSONDecodeError:
                pass
        
        return result