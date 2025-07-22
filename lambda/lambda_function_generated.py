import boto3
import json
import base64
import os
import logging
from datetime import datetime
from functools import lru_cache
from typing import Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# GENERATED FROM ACTUAL DATABASE SCHEMA
# Users table columns: ['id', 'email', 'first_name', 'last_name', 'phone', 'address_encrypted', 'date_of_birth_encrypted', 'ip_address_encrypted', 'ssn_encrypted', 'bank_account_encrypted', 'credit_card_encrypted', 'created_at', 'updated_at']
# Metadata table columns: ['id', 'user_id', 'field_name', 'pii_level', 'app_key_version', 'kms_key_alias', 'encryption_algorithm', 'encrypted_at']
# Audit table columns: ['id', 'user_id', 'field_name', 'pii_level', 'operation', 'accessed_by', 'ip_address', 'user_agent', 'request_id', 'success', 'error_message', 'error_code', 'operation_duration_ms', 'data_classification', 'retention_policy', 'accessed_at']
# Field mapping: {'email': 'email', 'first_name': 'first_name', 'last_name': 'last_name', 'phone': 'phone', 'address': 'address_encrypted', 'date_of_birth': 'date_of_birth_encrypted', 'ip_address': 'ip_address_encrypted', 'ssn': 'ssn_encrypted', 'bank_account': 'bank_account_encrypted', 'credit_card': 'credit_card_encrypted'}

class PIIClassifier:
    """Handles PII field classification into security levels"""
    
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
            'ssn', 'social_security_number', 'social_security', 'tax_id',
            'bank_account', 'account_number', 'routing_number',
            'credit_card', 'card_number', 'cvv', 'credit_card_number',
            'passport_number', 'drivers_license', 'national_id'
        ]
    }
    
    @classmethod
    def classify_pii_level(cls, field_name: str) -> int:
        """Determine PII level for given field name"""
        field_lower = field_name.lower().strip()
        
        for level, fields in cls.PII_LEVEL_MAPPING.items():
            if field_lower in fields:
                logger.info(f"Classified field '{field_name}' as Level {level}")
                return level
        
        logger.warning(f"Unknown field '{field_name}', defaulting to Level 1")
        return 1

class EncryptionHandler:
    """Handles encryption operations using exact database schema"""
    
    # EXACT FIELD MAPPING FROM DATABASE SCHEMA
    FIELD_MAPPING = {
        "email": "email",
        "first_name": "first_name",
        "last_name": "last_name",
        "phone": "phone",
        "address": "address_encrypted",
        "date_of_birth": "date_of_birth_encrypted",
        "ip_address": "ip_address_encrypted",
        "ssn": "ssn_encrypted",
        "bank_account": "bank_account_encrypted",
        "credit_card": "credit_card_encrypted"
}
    
    def __init__(self):
        self.kms = boto3.client('kms', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        self.secrets = boto3.client('secretsmanager', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
        
        self.level2_kms_alias = 'alias/pii-level2'
        self.level3_kms_alias = 'alias/pii-level3'
        self.db_credentials_secret = 'pii-database-credentials'
    
    @lru_cache(maxsize=1)
    def get_db_credentials(self) -> Dict[str, str]:
        """Retrieve database credentials from Secrets Manager"""
        try:
            response = self.secrets.get_secret_value(SecretId=self.db_credentials_secret)
            credentials = json.loads(response['SecretString'])
            logger.info("Successfully retrieved database credentials")
            return credentials
        except Exception as e:
            logger.error(f"Failed to retrieve database credentials: {str(e)}")
            raise
    
    def get_db_connection(self):
        """Create database connection"""
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
    
    def encrypt_field(self, field_name: str, value: str) -> Dict[str, Any]:
        """Encrypt field based on PII level using exact schema"""
        if value is None or value == '':
            db_field = self.FIELD_MAPPING.get(field_name, field_name)
            return {
                'db_field': db_field,
                'value': None,
                'encrypted': False,
                'level': 1,
                'field_name': field_name
            }
        
        level = PIIClassifier.classify_pii_level(field_name)
        db_field = self.FIELD_MAPPING.get(field_name, field_name)
        
        try:
            if level == 1:
                return {
                    'db_field': db_field,
                    'value': value,
                    'encrypted': False,
                    'level': 1,
                    'field_name': field_name,
                    'method': 'rds_only'
                }
                
            elif level == 2:
                response = self.kms.encrypt(
                    KeyId=self.level2_kms_alias,
                    Plaintext=value.encode('utf-8')
                )
                
                encrypted_value = base64.b64encode(response['CiphertextBlob']).decode('utf-8')
                
                return {
                    'db_field': db_field,
                    'value': encrypted_value,
                    'encrypted': True,
                    'level': 2,
                    'field_name': field_name,
                    'method': 'kms_level2',
                    'kms_key': self.level2_kms_alias
                }
                
            elif level == 3:
                response = self.kms.encrypt(
                    KeyId=self.level3_kms_alias,
                    Plaintext=value.encode('utf-8')
                )
                
                encrypted_value = base64.b64encode(response['CiphertextBlob']).decode('utf-8')
                
                return {
                    'db_field': db_field,
                    'value': encrypted_value,
                    'encrypted': True,
                    'level': 3,
                    'field_name': field_name,
                    'method': 'kms_level3',
                    'kms_key': self.level3_kms_alias
                }
                
        except Exception as e:
            logger.error(f"Encryption failed for field '{field_name}': {str(e)}")
            raise
    
    def decrypt_field(self, field_name: str, encrypted_value: str, level: int = None) -> str:
        """Decrypt field based on PII level"""
        if encrypted_value is None or encrypted_value == '':
            return encrypted_value
        
        if level is None:
            level = PIIClassifier.classify_pii_level(field_name)
        
        try:
            if level == 1:
                return encrypted_value
                
            elif level in [2, 3]:
                ciphertext = base64.b64decode(encrypted_value)
                response = self.kms.decrypt(CiphertextBlob=ciphertext)
                return response['Plaintext'].decode('utf-8')
                
        except Exception as e:
            logger.error(f"Decryption failed for field '{field_name}': {str(e)}")
            raise

class DatabaseOperations:
    """Handle database operations using EXACT schema"""
    
    def __init__(self, encryption_handler: EncryptionHandler):
        self.encryption_handler = encryption_handler
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user using EXACT database schema"""
        logger.info(f"Creating user with data: {list(user_data.keys())}")
        
        connection = None
        try:
            connection = self.encryption_handler.get_db_connection()
            cursor = connection.cursor()
            
            # Process fields according to exact schema
            insert_data = {}
            metadata_records = []
            
            for input_field, value in user_data.items():
                if input_field in self.encryption_handler.FIELD_MAPPING:
                    encryption_result = self.encryption_handler.encrypt_field(input_field, str(value) if value is not None else None)
                    db_field = encryption_result['db_field']
                    insert_data[db_field] = encryption_result['value']
                    
                    # Prepare metadata using EXACT column names
                    metadata_records.append({
                        'field_name': input_field,
                        'pii_level': encryption_result['level'],
                        'kms_key_alias': encryption_result.get('kms_key'),
                        'encryption_algorithm': encryption_result.get('method', 'none')
                    })
                else:
                    logger.warning(f"Unknown field: {input_field}")
            
            # Build INSERT query for users table using available fields
            available_fields = [field for field in insert_data.keys() if field in ['id', 'email', 'first_name', 'last_name', 'phone', 'address_encrypted', 'date_of_birth_encrypted', 'ip_address_encrypted', 'ssn_encrypted', 'bank_account_encrypted', 'credit_card_encrypted', 'created_at', 'updated_at']]
            if not available_fields:
                raise ValueError("No valid fields for user creation")
            
            fields_str = ', '.join(available_fields)
            placeholders = ', '.join([f'%({field})s' for field in available_fields])
            
            insert_query = f"INSERT INTO users ({fields_str}) VALUES ({placeholders}) RETURNING id, created_at"
            
            filtered_data = {k: v for k, v in insert_data.items() if k in available_fields}
            cursor.execute(insert_query, filtered_data)
            
            result = cursor.fetchone()
            user_id = result['id']
            created_at = result['created_at']
            
            # Insert metadata using EXACT column names: ['id', 'user_id', 'field_name', 'pii_level', 'app_key_version', 'kms_key_alias', 'encryption_algorithm', 'encrypted_at']
            for metadata in metadata_records:
                metadata_insert = """
                    INSERT INTO encryption_metadata (user_id, field_name, pii_level, kms_key_alias, encryption_algorithm)
                    VALUES (%(user_id)s, %(field_name)s, %(pii_level)s, %(kms_key_alias)s, %(encryption_algorithm)s)
                """
                
                cursor.execute(metadata_insert, {
                    'user_id': user_id,
                    'field_name': metadata['field_name'],
                    'pii_level': metadata['pii_level'],
                    'kms_key_alias': metadata['kms_key_alias'],
                    'encryption_algorithm': metadata['encryption_algorithm']
                })
            
            connection.commit()
            logger.info(f"Successfully created user with ID: {user_id}")
            
            return {
                'user_id': str(user_id),
                'created_at': created_at.isoformat(),
                'fields_processed': list(user_data.keys())
            }
            
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Failed to create user: {str(e)}")
            raise
        finally:
            if connection:
                connection.close()
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user using EXACT schema"""
        logger.info(f"Retrieving user with ID: {user_id}")
        
        connection = None
        try:
            connection = self.encryption_handler.get_db_connection()
            cursor = connection.cursor()
            
            # Select using exact column names
            user_columns = ['id', 'email', 'first_name', 'last_name', 'phone', 'address_encrypted', 'date_of_birth_encrypted', 'ip_address_encrypted', 'ssn_encrypted', 'bank_account_encrypted', 'credit_card_encrypted', 'created_at', 'updated_at']
            select_fields = ', '.join([col for col in user_columns if col != 'updated_at'])  # Skip if not needed
            
            user_query = f"SELECT {select_fields} FROM users WHERE id = %s"
            cursor.execute(user_query, (user_id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                return None
            
            # Get metadata
            metadata_query = "SELECT field_name, pii_level FROM encryption_metadata WHERE user_id = %s"
            cursor.execute(metadata_query, (user_id,))
            metadata_rows = cursor.fetchall()
            
            metadata_map = {row['field_name']: row['pii_level'] for row in metadata_rows}
            
            # Decrypt and format response
            result = {
                'user_id': str(user_data['id']),
                'created_at': user_data['created_at'].isoformat() if user_data.get('created_at') else None
            }
            
            # Map database fields back to input fields
            reverse_mapping = {
        "email": "email",
        "first_name": "first_name",
        "last_name": "last_name",
        "phone": "phone",
        "address_encrypted": "address",
        "date_of_birth_encrypted": "date_of_birth",
        "ip_address_encrypted": "ip_address",
        "ssn_encrypted": "ssn",
        "bank_account_encrypted": "bank_account",
        "credit_card_encrypted": "credit_card"
}
            
            for db_field, value in user_data.items():
                if db_field in ['id', 'created_at', 'updated_at']:
                    continue
                    
                input_field = reverse_mapping.get(db_field, db_field)
                
                if value is not None and input_field in metadata_map:
                    level = metadata_map[input_field]
                    if level > 1:
                        try:
                            decrypted = self.encryption_handler.decrypt_field(input_field, value, level)
                            result[input_field] = decrypted
                        except Exception as e:
                            logger.error(f"Decryption failed for {input_field}: {e}")
                            result[input_field] = "[DECRYPTION_FAILED]"
                    else:
                        result[input_field] = value
                else:
                    result[input_field] = value
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to retrieve user: {e}")
            raise
        finally:
            if connection:
                connection.close()
    
    def list_users(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """List users (Level 1 fields only)"""
        connection = None
        try:
            connection = self.encryption_handler.get_db_connection()
            cursor = connection.cursor()
            
            query = "SELECT id, email, first_name, last_name, created_at FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s"
            cursor.execute(query, (limit, offset))
            users = cursor.fetchall()
            
            cursor.execute("SELECT COUNT(*) as total FROM users")
            total = cursor.fetchone()['total']
            
            users_list = []
            for user in users:
                users_list.append({
                    'user_id': str(user['id']),
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'created_at': user['created_at'].isoformat() if user['created_at'] else None
                })
            
            return {
                'users': users_list,
                'total': total,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise
        finally:
            if connection:
                connection.close()
    
    def get_audit_trail(self, user_id: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Get audit trail using exact schema"""
        connection = None
        try:
            connection = self.encryption_handler.get_db_connection()
            cursor = connection.cursor()
            
            if user_id:
                query = """
                    SELECT id, user_id, operation, accessed_by, success, error_message, accessed_at
                    FROM encryption_audit WHERE user_id = %s ORDER BY accessed_at DESC LIMIT %s
                """
                cursor.execute(query, (user_id, limit))
            else:
                query = """
                    SELECT id, user_id, operation, accessed_by, success, error_message, accessed_at
                    FROM encryption_audit ORDER BY accessed_at DESC LIMIT %s
                """
                cursor.execute(query, (limit,))
            
            audit_logs = cursor.fetchall()
            
            formatted_logs = []
            for log in audit_logs:
                formatted_logs.append({
                    'audit_id': str(log['id']),
                    'user_id': str(log['user_id']) if log['user_id'] else None,
                    'operation': log['operation'],
                    'accessed_by': log['accessed_by'],
                    'success': log['success'],
                    'error_message': log['error_message'],
                    'timestamp': log['accessed_at'].isoformat() if log['accessed_at'] else None
                })
            
            return {
                'audit_logs': formatted_logs,
                'user_id': user_id,
                'limit': limit
            }
            
        except Exception as e:
            logger.error(f"Failed to get audit trail: {e}")
            raise
        finally:
            if connection:
                connection.close()

def lambda_handler(event, context):
    """Lambda handler with EXACT schema compatibility"""
    logger.info(f"Lambda invoked with event: {json.dumps(event, default=str)}")
    
    try:
        handler = EncryptionHandler()
        db_ops = DatabaseOperations(handler)
        operation = event.get('operation')
        
        if not operation:
            raise ValueError("Missing 'operation' in event")
        
        if operation == 'health':
            health_status = {
                'lambda': 'healthy',
                'kms': 'unknown',
                'secrets_manager': 'unknown',
                'database': 'unknown'
            }
            
            # Test KMS access
            try:
                handler.kms.describe_key(KeyId='alias/pii-level2')
                health_status['kms'] = 'healthy'
            except Exception as e:
                health_status['kms'] = f'error: {str(e)}'
            
            # Test Secrets Manager access
            try:
                handler.get_db_credentials()
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
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'health': health_status,
                    'timestamp': datetime.utcnow().isoformat(),
                    'success': True,
                    'schema_info': {
                        'users_columns': ['id', 'email', 'first_name', 'last_name', 'phone', 'address_encrypted', 'date_of_birth_encrypted', 'ip_address_encrypted', 'ssn_encrypted', 'bank_account_encrypted', 'credit_card_encrypted', 'created_at', 'updated_at'],
                        'metadata_columns': ['id', 'user_id', 'field_name', 'pii_level', 'app_key_version', 'kms_key_alias', 'encryption_algorithm', 'encrypted_at'],
                        'field_mapping': {"email": "email", "first_name": "first_name", "last_name": "last_name", "phone": "phone", "address": "address_encrypted", "date_of_birth": "date_of_birth_encrypted", "ip_address": "ip_address_encrypted", "ssn": "ssn_encrypted", "bank_account": "bank_account_encrypted", "credit_card": "credit_card_encrypted"}
                    }
                })
            }
        
        elif operation == 'create_user':
            user_data = event.get('data', {})
            if not user_data:
                raise ValueError("Missing 'data' for create_user operation")
            
            result = db_ops.create_user(user_data)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'operation': 'create_user',
                    'result': result,
                    'success': True
                })
            }
        
        elif operation == 'get_user':
            user_id = event.get('user_id')
            if not user_id:
                raise ValueError("Missing 'user_id' for get_user operation")
            
            result = db_ops.get_user(str(user_id))
            
            if result is None:
                return {
                    'statusCode': 404,
                    'body': json.dumps({
                        'error': 'User not found',
                        'user_id': user_id,
                        'success': False
                    })
                }
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'operation': 'get_user',
                    'result': result,
                    'success': True
                }, default=str)
            }
        
        elif operation == 'list_users':
            limit = event.get('limit', 10)
            offset = event.get('offset', 0)
            
            result = db_ops.list_users(limit, offset)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'operation': 'list_users',
                    'result': result,
                    'success': True
                }, default=str)
            }
        
        elif operation == 'audit_trail':
            user_id = event.get('user_id')
            limit = event.get('limit', 100)
            
            result = db_ops.get_audit_trail(user_id, limit)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'operation': 'audit_trail',
                    'result': result,
                    'success': True
                }, default=str)
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f'Unknown operation: {operation}',
                    'supported_operations': ['health', 'create_user', 'get_user', 'list_users', 'audit_trail'],
                    'success': False
                })
            }
            
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
