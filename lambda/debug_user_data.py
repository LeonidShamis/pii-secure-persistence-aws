#!/usr/bin/env python3
"""
Debug script to check what's actually stored in the database
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from pathlib import Path

def get_database_connection():
    """Get database connection"""
    database_dir = Path(__file__).parent.parent / "database"
    env_file = database_dir / ".env"
    
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"').strip("'")
    
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'sslmode': os.getenv('DB_SSLMODE', 'prefer')
    }
    
    return psycopg2.connect(**db_config, cursor_factory=RealDictCursor)

def debug_user_data():
    """Debug what's actually stored"""
    
    conn = get_database_connection()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🔍 DEBUGGING USER DATA")
    print("=" * 60)
    
    # Get the most recent user
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 1")
    user = cursor.fetchone()
    
    if not user:
        print("❌ No users found")
        return
    
    print(f"📋 User ID: {user['id']}")
    print(f"📅 Created: {user['created_at']}")
    
    print("\n🔍 STORED VALUES:")
    for field, value in user.items():
        if field not in ['id', 'created_at', 'updated_at']:
            value_str = str(value)[:50] + "..." if value and len(str(value)) > 50 else str(value)
            print(f"  {field}: {value_str}")
            
            # Check if it looks like base64
            if value and isinstance(value, str) and len(value) > 10:
                try:
                    import base64
                    decoded = base64.b64decode(value)
                    print(f"    → Base64 decoded length: {len(decoded)} bytes")
                except Exception as e:
                    print(f"    → Not valid base64: {e}")
    
    # Check metadata
    print(f"\n🔍 METADATA for user {user['id']}:")
    cursor.execute("SELECT * FROM encryption_metadata WHERE user_id = %s", (user['id'],))
    metadata_rows = cursor.fetchall()
    
    for metadata in metadata_rows:
        print(f"  {metadata['field_name']}: Level {metadata['pii_level']}")
        print(f"    Algorithm: {metadata['encryption_algorithm']}")
        print(f"    KMS Key: {metadata['kms_key_alias']}")
    
    # Check what was actually inserted
    print(f"\n🔍 RAW DATABASE QUERY:")
    cursor.execute("""
        SELECT email, first_name, last_name, phone, 
               address_encrypted, date_of_birth_encrypted, 
               ssn_encrypted, bank_account_encrypted
        FROM users WHERE id = %s
    """, (user['id'],))
    
    raw_data = cursor.fetchone()
    print("Raw field values:")
    for field, value in raw_data.items():
        print(f"  {field}: '{value}'")
    
    conn.close()

if __name__ == "__main__":
    debug_user_data()