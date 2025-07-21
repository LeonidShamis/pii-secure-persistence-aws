"""
PII Encryption Lambda Function

This Lambda function handles three-tier encryption for PII data:
- Level 1 (Low Sensitivity): Names, emails, phone numbers - RDS at-rest encryption only
- Level 2 (Medium Sensitivity): Addresses, dates of birth, IP addresses - Field-level encryption using AWS KMS CMK
- Level 3 (High Sensitivity): SSN, bank accounts, credit cards - Double encryption (Application-layer + AWS KMS CMK)
"""

import boto3
import json
import base64
import os
import logging
from datetime import datetime
from functools import lru_cache
from typing import Dict, Any, Optional, Tuple
from cryptography.fernet import Fernet
import psycopg2
from psycopg2.extras import RealDictCursor

from .database_operations import DatabaseManager

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class PIIClassifier:
    """Handles PII field classification into three security levels"""
    
    # PII level mapping based on sensitivity
    PII_LEVEL_MAPPING = {
        1: [
            'email', 'first_name', 'last_name', 'phone', 'phone_number',
            'name', 'username', 'display_name'
        ],
        2: [
            'address', 'street_address', 'city', 'state', 'zip_code', 'postal_code',
            'date_of_birth', 'dob', 'birth_date', 'ip_address', 'location',
            'country', 'region', 'timezone'
        ],
        3: [
            'ssn', 'social_security_number', 'bank_account', 'account_number',
            'credit_card', 'credit_card_number', 'medical_record', 'health_record',
            'passport_number', 'driver_license', 'tax_id', 'national_id'
        ]
    }
    
    @classmethod
    def classify_pii_level(cls, field_name: str) -> int:
        """
        Determine PII level based on field name
        
        Args:
            field_name: Name of the field to classify
            
        Returns:
            int: PII level (1, 2, or 3)
        """
        field_lower = field_name.lower().strip()
        
        for level, fields in cls.PII_LEVEL_MAPPING.items():
            if field_lower in fields:
                logger.info(f"Classified field '{field_name}' as Level {level}")
                return level
        
        # Default to level 1 for unknown fields
        logger.warning(f"Unknown field '{field_name}', defaulting to Level 1")
        return 1
    
    @classmethod
    def get_encryption_requirements(cls, field_name: str) -> Dict[str, Any]:
        """
        Get encryption requirements for a field
        
        Args:
            field_name: Name of the field
            
        Returns:
            dict: Encryption requirements
        """
        level = cls.classify_pii_level(field_name)
        
        requirements = {
            'level': level,
            'field_name': field_name,
            'requires_kms': level >= 2,
            'requires_app_encryption': level == 3,
            'storage_suffix': '_encrypted' if level > 1 else ''
        }
        
        return requirements


class EncryptionHandler:
    """Handles all encryption and decryption operations for PII data"""
    
    def __init__(self):
        self.kms = boto3.client('kms', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        self.secrets = boto3.client('secretsmanager', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        self._secrets_cache = {}
        
        # KMS key aliases for different levels
        self.level2_kms_alias = 'alias/pii-level2'
        self.level3_kms_alias = 'alias/pii-level3'
        
        # Secrets Manager secret names
        self.app_keys_secret = 'pii-encryption-keys'
        self.db_credentials_secret = 'pii-database-credentials'
    
    @lru_cache(maxsize=1)
    def get_app_keys(self) -> Dict[str, Any]:
        """
        Retrieve and cache application encryption keys from Secrets Manager
        
        Returns:
            dict: Application encryption keys
        """
        try:
            response = self.secrets.get_secret_value(SecretId=self.app_keys_secret)
            secret_data = json.loads(response['SecretString'])
            logger.info("Successfully retrieved application encryption keys")
            return secret_data['app_encryption_keys']
        except Exception as e:
            logger.error(f"Failed to retrieve application keys: {str(e)}")
            raise
    
    @lru_cache(maxsize=1)
    def get_db_credentials(self) -> Dict[str, str]:
        """
        Retrieve database credentials from Secrets Manager
        
        Returns:
            dict: Database connection credentials
        """
        try:
            response = self.secrets.get_secret_value(SecretId=self.db_credentials_secret)
            credentials = json.loads(response['SecretString'])
            logger.info("Successfully retrieved database credentials")
            return credentials
        except Exception as e:
            logger.error(f"Failed to retrieve database credentials: {str(e)}")
            raise
    
    def get_db_connection(self):
        """
        Create database connection using cached credentials
        
        Returns:
            psycopg2.connection: Database connection
        """
        try:
            creds = self.get_db_credentials()
            connection = psycopg2.connect(
                host=creds['host'],
                port=creds['port'],
                database=creds['database'],
                user=creds['username'],
                password=creds['password'],
                cursor_factory=RealDictCursor,
                connect_timeout=10
            )
            logger.info("Successfully connected to database")
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def get_current_app_cipher(self) -> Fernet:
        """
        Get Fernet cipher for current application key version
        
        Returns:
            Fernet: Cipher for encryption/decryption
        """
        try:
            keys = self.get_app_keys()
            current_version = keys['current_version']
            key = keys[f'level3_app_key_v{current_version}']
            return Fernet(key.encode())
        except Exception as e:
            logger.error(f"Failed to get current app cipher: {str(e)}")
            raise
    
    def get_app_cipher_for_version(self, version: int) -> Fernet:
        """
        Get Fernet cipher for specific key version
        
        Args:
            version: Key version number
            
        Returns:
            Fernet: Cipher for decryption
        """
        try:
            keys = self.get_app_keys()
            key = keys[f'level3_app_key_v{version}']
            return Fernet(key.encode())
        except Exception as e:
            logger.error(f"Failed to get app cipher for version {version}: {str(e)}")
            raise
    
    def encrypt_field(self, field_name: str, value: str) -> Dict[str, Any]:
        """
        Encrypt field based on its PII level
        
        Args:
            field_name: Name of the field
            value: Value to encrypt
            
        Returns:
            dict: Encryption result with metadata
        """
        if value is None or value == '':
            return {
                'value': None,
                'encrypted': False,
                'level': 1,
                'field_name': field_name
            }
        
        requirements = PIIClassifier.get_encryption_requirements(field_name)
        level = requirements['level']
        
        try:
            if level == 1:
                # Level 1: Pass-through (RDS at-rest encryption only)
                return {
                    'value': value,
                    'encrypted': False,
                    'level': 1,
                    'field_name': field_name,
                    'method': 'rds_only'
                }
                
            elif level == 2:
                # Level 2: KMS encryption only
                response = self.kms.encrypt(
                    KeyId=self.level2_kms_alias,
                    Plaintext=value.encode('utf-8')
                )
                
                encrypted_value = base64.b64encode(response['CiphertextBlob']).decode('utf-8')
                
                return {
                    'value': encrypted_value,
                    'encrypted': True,
                    'level': 2,
                    'field_name': field_name,
                    'method': 'kms_only',
                    'kms_key': self.level2_kms_alias
                }
                
            elif level == 3:
                # Level 3: Double encryption (App + KMS)
                # Step 1: Application-layer encryption
                cipher = self.get_current_app_cipher()
                app_encrypted = cipher.encrypt(value.encode('utf-8'))
                
                # Step 2: KMS encryption of app-encrypted data
                response = self.kms.encrypt(
                    KeyId=self.level3_kms_alias,
                    Plaintext=app_encrypted
                )
                
                final_encrypted_value = base64.b64encode(response['CiphertextBlob']).decode('utf-8')
                
                return {
                    'value': final_encrypted_value,
                    'encrypted': True,
                    'level': 3,
                    'field_name': field_name,
                    'method': 'double_encryption',
                    'app_key_version': self.get_app_keys()['current_version'],
                    'kms_key': self.level3_kms_alias
                }
            
        except Exception as e:
            logger.error(f"Encryption failed for field '{field_name}' (Level {level}): {str(e)}")
            raise
    
    def decrypt_field(self, field_name: str, encrypted_value: str, metadata: Optional[Dict] = None) -> str:
        """
        Decrypt field based on its PII level and metadata
        
        Args:
            field_name: Name of the field
            encrypted_value: Encrypted value to decrypt
            metadata: Encryption metadata
            
        Returns:
            str: Decrypted value
        """
        if encrypted_value is None or encrypted_value == '':
            return encrypted_value
        
        requirements = PIIClassifier.get_encryption_requirements(field_name)
        level = requirements['level']
        
        # Override level from metadata if available
        if metadata and 'level' in metadata:
            level = metadata['level']
        
        try:
            if level == 1:
                # Level 1: No decryption needed
                return encrypted_value
                
            elif level == 2:
                # Level 2: KMS decryption only
                ciphertext = base64.b64decode(encrypted_value)
                response = self.kms.decrypt(CiphertextBlob=ciphertext)
                return response['Plaintext'].decode('utf-8')
                
            elif level == 3:
                # Level 3: Double decryption (KMS then App)
                # Step 1: KMS decryption
                ciphertext = base64.b64decode(encrypted_value)
                response = self.kms.decrypt(CiphertextBlob=ciphertext)
                
                # Step 2: Application-layer decryption
                app_key_version = metadata.get('app_key_version', 1) if metadata else 1
                cipher = self.get_app_cipher_for_version(app_key_version)
                
                decrypted_value = cipher.decrypt(response['Plaintext']).decode('utf-8')
                return decrypted_value
                
        except Exception as e:
            logger.error(f"Decryption failed for field '{field_name}' (Level {level}): {str(e)}")
            raise
    
    def log_audit(self, user_id: str, field_name: str, operation: str, 
                  success: bool = True, error: str = None, ip_address: str = None):
        """
        Log encryption/decryption operations for audit trail
        
        Args:
            user_id: User ID
            field_name: Field name that was operated on
            operation: Operation type (encrypt/decrypt)
            success: Whether operation was successful
            error: Error message if failed
            ip_address: Client IP address
        """
        try:
            conn = self.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO encryption_audit (
                        user_id, field_name, pii_level, operation,
                        accessed_by, ip_address, success, error_message
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id, 
                    field_name, 
                    PIIClassifier.classify_pii_level(field_name),
                    operation, 
                    'lambda-encryption-service',
                    ip_address,
                    success, 
                    error
                ))
                conn.commit()
                logger.info(f"Audit log created: {operation} {field_name} for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to log audit entry: {str(e)}")
            # Don't raise exception for audit logging failures
        finally:
            if 'conn' in locals():
                conn.close()


def lambda_handler(event, context):
    """
    Main Lambda entry point for PII encryption operations
    
    Args:
        event: Lambda event containing operation and data
        context: Lambda context
        
    Returns:
        dict: Response with status and data
    """
    logger.info(f"Lambda invoked with event: {json.dumps(event, default=str)}")
    
    try:
        handler = EncryptionHandler()
        db_manager = DatabaseManager(handler)
        operation = event.get('operation')
        
        if not operation:
            raise ValueError("Missing 'operation' in event")
        
        if operation == 'create_user':
            return handle_create_user_operation(handler, db_manager, event)
        elif operation == 'get_user':
            return handle_get_user_operation(handler, db_manager, event)
        elif operation == 'encrypt':
            return handle_encrypt_operation(handler, event)
        elif operation == 'decrypt':
            return handle_decrypt_operation(handler, event)
        elif operation == 'health':
            return handle_health_check(handler, db_manager)
        elif operation == 'list_users':
            return handle_list_users_operation(db_manager, event)
        elif operation == 'delete_user':
            return handle_delete_user_operation(db_manager, event)
        elif operation == 'audit_trail':
            return handle_audit_trail_operation(db_manager, event)
        else:
            raise ValueError(f"Unknown operation: {operation}")
            
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'type': type(e).__name__,
                'success': False
            })
        }


def handle_encrypt_operation(handler: EncryptionHandler, event: Dict) -> Dict:
    """Handle encryption operation"""
    data = event.get('data', {})
    if not data:
        raise ValueError("Missing 'data' in encrypt operation")
    
    encrypted_result = {
        'fields': {},
        'metadata': {}
    }
    
    # Process each field
    for field_name, value in data.items():
        if value is None:
            continue
            
        try:
            result = handler.encrypt_field(field_name, str(value))
            
            if result['level'] == 1:
                # Level 1 fields stored as-is
                encrypted_result['fields'][field_name] = result['value']
            else:
                # Level 2/3 fields stored with _encrypted suffix
                encrypted_result['fields'][f"{field_name}_encrypted"] = result['value']
                encrypted_result['metadata'][field_name] = {
                    'level': result['level'],
                    'method': result['method'],
                    'app_key_version': result.get('app_key_version'),
                    'kms_key': result.get('kms_key')
                }
                
        except Exception as e:
            logger.error(f"Failed to encrypt field {field_name}: {str(e)}")
            raise
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'encrypted_data': encrypted_result,
            'success': True,
            'processed_fields': len(data)
        })
    }


def handle_decrypt_operation(handler: EncryptionHandler, event: Dict) -> Dict:
    """Handle decryption operation"""
    encrypted_data = event.get('encrypted_data', {})
    metadata = event.get('metadata', {})
    
    if not encrypted_data:
        raise ValueError("Missing 'encrypted_data' in decrypt operation")
    
    decrypted_result = {}
    
    # Process each field
    for field_name, value in encrypted_data.items():
        if value is None:
            continue
            
        try:
            if field_name.endswith('_encrypted'):
                # This is an encrypted field - decrypt it
                original_field = field_name.replace('_encrypted', '')
                field_metadata = metadata.get(original_field, {})
                
                decrypted_value = handler.decrypt_field(
                    original_field, 
                    value, 
                    field_metadata
                )
                decrypted_result[original_field] = decrypted_value
            else:
                # This is a Level 1 field - pass through
                decrypted_result[field_name] = value
                
        except Exception as e:
            logger.error(f"Failed to decrypt field {field_name}: {str(e)}")
            raise
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'decrypted_data': decrypted_result,
            'success': True,
            'processed_fields': len(encrypted_data)
        })
    }


def handle_health_check(handler: EncryptionHandler, db_manager: DatabaseManager) -> Dict:
    """Handle health check operation"""
    health_status = {
        'lambda': 'healthy',
        'kms': 'unknown',
        'secrets_manager': 'unknown',
        'database': 'unknown',
        'database_schema': 'unknown'
    }
    
    # Test KMS access
    try:
        handler.kms.describe_key(KeyId='alias/pii-level2')
        health_status['kms'] = 'healthy'
    except Exception as e:
        health_status['kms'] = f'error: {str(e)}'
    
    # Test Secrets Manager access
    try:
        handler.get_app_keys()
        health_status['secrets_manager'] = 'healthy'
    except Exception as e:
        health_status['secrets_manager'] = f'error: {str(e)}'
    
    # Test database connection
    try:
        conn = handler.get_db_connection()
        conn.close()
        health_status['database'] = 'healthy'
    except Exception as e:
        health_status['database'] = f'error: {str(e)}'
    
    # Test database schema
    try:
        schema_validation = db_manager.validate_database_schema()
        if schema_validation.get('overall', False):
            health_status['database_schema'] = 'healthy'
        else:
            health_status['database_schema'] = f'validation failed: {schema_validation}'
    except Exception as e:
        health_status['database_schema'] = f'error: {str(e)}'
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'health': health_status,
            'timestamp': datetime.utcnow().isoformat(),
            'success': True
        })
    }


def handle_create_user_operation(handler: EncryptionHandler, db_manager: DatabaseManager, event: Dict) -> Dict:
    """Handle create user operation with encryption and database storage"""
    data = event.get('data', {})
    if not data:
        raise ValueError("Missing 'data' in create_user operation")
    
    # Encrypt all fields
    encrypted_result = {
        'fields': {},
        'metadata': {}
    }
    
    for field_name, value in data.items():
        if value is None:
            continue
            
        try:
            result = handler.encrypt_field(field_name, str(value))
            
            if result['level'] == 1:
                encrypted_result['fields'][field_name] = result['value']
            else:
                encrypted_result['fields'][f"{field_name}_encrypted"] = result['value']
                encrypted_result['metadata'][field_name] = {
                    'level': result['level'],
                    'method': result['method'],
                    'app_key_version': result.get('app_key_version'),
                    'kms_key': result.get('kms_key')
                }
                
        except Exception as e:
            logger.error(f"Failed to encrypt field {field_name}: {str(e)}")
            raise
    
    # Store in database
    user_id = db_manager.store_encrypted_user(encrypted_result)
    
    # Log audit trail for each field
    for field_name in data.keys():
        try:
            handler.log_audit(user_id, field_name, 'encrypt', success=True)
        except Exception as e:
            logger.warning(f"Failed to log audit for field {field_name}: {str(e)}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'user_id': user_id,
            'success': True,
            'processed_fields': len(data),
            'message': 'User created and encrypted successfully'
        })
    }


def handle_get_user_operation(handler: EncryptionHandler, db_manager: DatabaseManager, event: Dict) -> Dict:
    """Handle get user operation with decryption"""
    user_id = event.get('user_id')
    if not user_id:
        raise ValueError("Missing 'user_id' in get_user operation")
    
    # Retrieve encrypted data from database
    encrypted_data, metadata = db_manager.retrieve_encrypted_user(user_id)
    
    # Decrypt all fields
    decrypted_result = {}
    
    for field_name, value in encrypted_data.items():
        if value is None:
            continue
            
        try:
            if field_name.endswith('_encrypted'):
                original_field = field_name.replace('_encrypted', '')
                field_metadata = metadata.get(original_field, {})
                
                decrypted_value = handler.decrypt_field(
                    original_field, 
                    value, 
                    field_metadata
                )
                decrypted_result[original_field] = decrypted_value
                
                # Log audit trail
                try:
                    handler.log_audit(user_id, original_field, 'decrypt', success=True)
                except Exception as e:
                    logger.warning(f"Failed to log audit for field {original_field}: {str(e)}")
            else:
                decrypted_result[field_name] = value
                
        except Exception as e:
            logger.error(f"Failed to decrypt field {field_name}: {str(e)}")
            raise
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'user_id': user_id,
            'data': decrypted_result,
            'success': True,
            'processed_fields': len(encrypted_data)
        })
    }


def handle_list_users_operation(db_manager: DatabaseManager, event: Dict) -> Dict:
    """Handle list users operation"""
    limit = event.get('limit', 100)
    offset = event.get('offset', 0)
    
    result = db_manager.list_users(limit=limit, offset=offset)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'users': result['users'],
            'pagination': {
                'total': result['total'],
                'limit': result['limit'],
                'offset': result['offset'],
                'has_more': result['offset'] + len(result['users']) < result['total']
            },
            'success': True
        })
    }


def handle_delete_user_operation(db_manager: DatabaseManager, event: Dict) -> Dict:
    """Handle delete user operation (crypto-shredding)"""
    user_id = event.get('user_id')
    if not user_id:
        raise ValueError("Missing 'user_id' in delete_user operation")
    
    success = db_manager.delete_user(user_id)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'user_id': user_id,
            'deleted': success,
            'success': True,
            'message': 'User deleted successfully (crypto-shredding completed)'
        })
    }


def handle_audit_trail_operation(db_manager: DatabaseManager, event: Dict) -> Dict:
    """Handle audit trail retrieval operation"""
    user_id = event.get('user_id')
    limit = event.get('limit', 100)
    
    result = db_manager.get_audit_trail(user_id=user_id, limit=limit)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'audit_records': result['audit_records'],
            'total': result['total'],
            'user_id': result['user_id'],
            'limit': result['limit'],
            'success': True
        })
    }