"""
Database operations module for PII encryption system

Handles all database CRUD operations for encrypted user data,
metadata, and audit logging.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Handles all database operations for the PII encryption system"""
    
    def __init__(self, encryption_handler):
        """
        Initialize with encryption handler for database credentials
        
        Args:
            encryption_handler: EncryptionHandler instance for credentials
        """
        self.encryption_handler = encryption_handler
    
    def get_connection(self):
        """Get database connection using encryption handler credentials"""
        return self.encryption_handler.get_db_connection()
    
    def store_encrypted_user(self, encrypted_data: Dict[str, Any]) -> str:
        """
        Store encrypted user data in database
        
        Args:
            encrypted_data: Dictionary containing encrypted fields and metadata
            
        Returns:
            str: User ID of created record
            
        Raises:
            Exception: If database operation fails
        """
        conn = None
        try:
            conn = self.get_connection()
            
            with conn.cursor() as cursor:
                # Prepare user data for insertion
                user_fields = encrypted_data.get('fields', {})
                metadata = encrypted_data.get('metadata', {})
                
                # Build dynamic insert query based on available fields
                insert_fields = []
                insert_values = []
                insert_placeholders = []
                
                # Define all possible fields and their mapping
                field_mapping = {
                    # Level 1 fields (stored as-is)
                    'email': 'email',
                    'first_name': 'first_name', 
                    'last_name': 'last_name',
                    'phone': 'phone',
                    
                    # Level 2 fields (stored with _encrypted suffix)
                    'address_encrypted': 'address_encrypted',
                    'dob_encrypted': 'dob_encrypted',
                    'date_of_birth_encrypted': 'dob_encrypted',  # alias
                    
                    # Level 3 fields (stored with _encrypted suffix)
                    'ssn_encrypted': 'ssn_encrypted',
                    'bank_account_encrypted': 'bank_account_encrypted',
                    'credit_card_encrypted': 'credit_card_encrypted'
                }
                
                # Process each field in user data
                for field_name, value in user_fields.items():
                    if field_name in field_mapping and value is not None:
                        db_column = field_mapping[field_name]
                        insert_fields.append(db_column)
                        insert_values.append(value)
                        insert_placeholders.append('%s')
                
                if not insert_fields:
                    raise ValueError("No valid fields to insert")
                
                # Build and execute insert query
                insert_query = f"""
                    INSERT INTO users ({', '.join(insert_fields)})
                    VALUES ({', '.join(insert_placeholders)})
                    RETURNING id
                """
                
                logger.info(f"Executing insert query for {len(insert_fields)} fields")
                cursor.execute(insert_query, insert_values)
                user_id = cursor.fetchone()['id']
                
                # Insert metadata for encrypted fields
                for original_field, field_metadata in metadata.items():
                    self._insert_metadata(cursor, user_id, original_field, field_metadata)
                
                conn.commit()
                logger.info(f"Successfully stored user with ID: {user_id}")
                return str(user_id)
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to store encrypted user: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def retrieve_encrypted_user(self, user_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Retrieve encrypted user data and metadata from database
        
        Args:
            user_id: User ID to retrieve
            
        Returns:
            Tuple[Dict, Dict]: (user_data, metadata)
            
        Raises:
            Exception: If user not found or database operation fails
        """
        conn = None
        try:
            conn = self.get_connection()
            
            with conn.cursor() as cursor:
                # Get user data
                cursor.execute(
                    "SELECT * FROM users WHERE id = %s",
                    (user_id,)
                )
                user_data = cursor.fetchone()
                
                if not user_data:
                    raise ValueError(f"User with ID {user_id} not found")
                
                # Convert to regular dict and remove system fields
                user_dict = dict(user_data)
                system_fields = ['id', 'created_at', 'updated_at']
                for field in system_fields:
                    user_dict.pop(field, None)
                
                # Get metadata for encrypted fields
                cursor.execute(
                    "SELECT * FROM encryption_metadata WHERE user_id = %s",
                    (user_id,)
                )
                metadata_rows = cursor.fetchall()
                
                # Build metadata dictionary
                metadata = {}
                for row in metadata_rows:
                    metadata[row['field_name']] = {
                        'level': row['pii_level'],
                        'app_key_version': row['app_key_version'],
                        'kms_key_alias': row['kms_key_alias']
                    }
                
                logger.info(f"Successfully retrieved user {user_id} with {len(metadata)} encrypted fields")
                return user_dict, metadata
                
        except Exception as e:
            logger.error(f"Failed to retrieve user {user_id}: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def update_user_field(self, user_id: str, field_name: str, encrypted_value: str, 
                         metadata: Dict[str, Any]) -> bool:
        """
        Update a specific encrypted field for a user
        
        Args:
            user_id: User ID
            field_name: Field name to update
            encrypted_value: New encrypted value
            metadata: Field metadata
            
        Returns:
            bool: Success status
        """
        conn = None
        try:
            conn = self.get_connection()
            
            with conn.cursor() as cursor:
                # Determine database column name
                column_name = field_name
                if metadata.get('level', 1) > 1:
                    column_name = f"{field_name}_encrypted"
                
                # Update user record
                update_query = f"UPDATE users SET {column_name} = %s, updated_at = NOW() WHERE id = %s"
                cursor.execute(update_query, (encrypted_value, user_id))
                
                if cursor.rowcount == 0:
                    raise ValueError(f"User {user_id} not found")
                
                # Update or insert metadata
                if metadata.get('level', 1) > 1:
                    self._upsert_metadata(cursor, user_id, field_name, metadata)
                
                conn.commit()
                logger.info(f"Successfully updated field {field_name} for user {user_id}")
                return True
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to update field {field_name} for user {user_id}: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def delete_user(self, user_id: str) -> bool:
        """
        Delete user and all associated metadata (crypto-shredding)
        
        Args:
            user_id: User ID to delete
            
        Returns:
            bool: Success status
        """
        conn = None
        try:
            conn = self.get_connection()
            
            with conn.cursor() as cursor:
                # Delete user (metadata will be deleted by CASCADE)
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                
                if cursor.rowcount == 0:
                    raise ValueError(f"User {user_id} not found")
                
                conn.commit()
                logger.info(f"Successfully deleted user {user_id}")
                return True
                
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to delete user {user_id}: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def list_users(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        List users with basic information (no sensitive data)
        
        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            dict: List of users with metadata
        """
        conn = None
        try:
            conn = self.get_connection()
            
            with conn.cursor() as cursor:
                # Get basic user info without sensitive fields
                cursor.execute("""
                    SELECT id, email, first_name, last_name, created_at, updated_at
                    FROM users 
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, offset))
                
                users = cursor.fetchall()
                
                # Get total count
                cursor.execute("SELECT COUNT(*) as total FROM users")
                total = cursor.fetchone()['total']
                
                result = {
                    'users': [dict(user) for user in users],
                    'total': total,
                    'limit': limit,
                    'offset': offset
                }
                
                logger.info(f"Retrieved {len(users)} users (total: {total})")
                return result
                
        except Exception as e:
            logger.error(f"Failed to list users: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def get_audit_trail(self, user_id: Optional[str] = None, 
                       limit: int = 100) -> Dict[str, Any]:
        """
        Retrieve audit trail for encryption operations
        
        Args:
            user_id: Optional user ID to filter by
            limit: Maximum number of records
            
        Returns:
            dict: Audit trail records
        """
        conn = None
        try:
            conn = self.get_connection()
            
            with conn.cursor() as cursor:
                if user_id:
                    cursor.execute("""
                        SELECT * FROM encryption_audit 
                        WHERE user_id = %s
                        ORDER BY accessed_at DESC
                        LIMIT %s
                    """, (user_id, limit))
                else:
                    cursor.execute("""
                        SELECT * FROM encryption_audit 
                        ORDER BY accessed_at DESC
                        LIMIT %s
                    """, (limit,))
                
                audit_records = cursor.fetchall()
                
                result = {
                    'audit_records': [dict(record) for record in audit_records],
                    'total': len(audit_records),
                    'user_id': user_id,
                    'limit': limit
                }
                
                logger.info(f"Retrieved {len(audit_records)} audit records")
                return result
                
        except Exception as e:
            logger.error(f"Failed to retrieve audit trail: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _insert_metadata(self, cursor, user_id: str, field_name: str, 
                        metadata: Dict[str, Any]):
        """Insert encryption metadata for a field"""
        cursor.execute("""
            INSERT INTO encryption_metadata (
                user_id, field_name, pii_level, 
                app_key_version, kms_key_alias
            ) VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id,
            field_name,
            metadata.get('level'),
            metadata.get('app_key_version'),
            metadata.get('kms_key')
        ))
    
    def _upsert_metadata(self, cursor, user_id: str, field_name: str, 
                        metadata: Dict[str, Any]):
        """Update or insert encryption metadata for a field"""
        cursor.execute("""
            INSERT INTO encryption_metadata (
                user_id, field_name, pii_level, 
                app_key_version, kms_key_alias
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (user_id, field_name) 
            DO UPDATE SET
                pii_level = EXCLUDED.pii_level,
                app_key_version = EXCLUDED.app_key_version,
                kms_key_alias = EXCLUDED.kms_key_alias,
                encrypted_at = NOW()
        """, (
            user_id,
            field_name,
            metadata.get('level'),
            metadata.get('app_key_version'),
            metadata.get('kms_key')
        ))
    
    def validate_database_schema(self) -> Dict[str, bool]:
        """
        Validate that required database tables and columns exist
        
        Returns:
            dict: Validation results for each component
        """
        conn = None
        validation_results = {}
        
        try:
            conn = self.get_connection()
            
            with conn.cursor() as cursor:
                # Check users table
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'users' AND table_schema = 'public'
                """)
                user_columns = [row['column_name'] for row in cursor.fetchall()]
                
                required_user_columns = [
                    'id', 'email', 'first_name', 'last_name', 
                    'address_encrypted', 'dob_encrypted', 'ssn_encrypted',
                    'bank_account_encrypted', 'created_at', 'updated_at'
                ]
                
                validation_results['users_table'] = all(
                    col in user_columns for col in required_user_columns
                )
                
                # Check metadata table
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'encryption_metadata' AND table_schema = 'public'
                """)
                metadata_columns = [row['column_name'] for row in cursor.fetchall()]
                
                required_metadata_columns = [
                    'id', 'user_id', 'field_name', 'pii_level',
                    'app_key_version', 'kms_key_alias', 'encrypted_at'
                ]
                
                validation_results['metadata_table'] = all(
                    col in metadata_columns for col in required_metadata_columns
                )
                
                # Check audit table
                cursor.execute("""
                    SELECT column_name FROM information_schema.columns 
                    WHERE table_name = 'encryption_audit' AND table_schema = 'public'
                """)
                audit_columns = [row['column_name'] for row in cursor.fetchall()]
                
                required_audit_columns = [
                    'id', 'user_id', 'field_name', 'pii_level', 'operation',
                    'accessed_by', 'success', 'accessed_at'
                ]
                
                validation_results['audit_table'] = all(
                    col in audit_columns for col in required_audit_columns
                )
                
                validation_results['overall'] = all(validation_results.values())
                
                logger.info(f"Database schema validation: {validation_results}")
                return validation_results
                
        except Exception as e:
            logger.error(f"Database schema validation failed: {str(e)}")
            validation_results['error'] = str(e)
            return validation_results
        finally:
            if conn:
                conn.close()


def extend_lambda_with_database_ops(handler):
    """
    Extend the main Lambda handler with database operations
    
    Args:
        handler: EncryptionHandler instance
        
    Returns:
        DatabaseManager: Database manager instance
    """
    return DatabaseManager(handler)