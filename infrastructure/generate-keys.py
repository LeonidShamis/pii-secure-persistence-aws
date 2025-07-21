#!/usr/bin/env python3
"""
Generate encryption keys for PII encryption system
Run this to generate keys for Secrets Manager setup
"""

import secrets
import base64
import json
from cryptography.fernet import Fernet

def generate_fernet_key():
    """Generate a Fernet key for application-layer encryption"""
    return Fernet.generate_key().decode()

def generate_random_password(length=32):
    """Generate a secure random password"""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def main():
    print("=== PII Encryption System Key Generation ===\n")
    
    # Generate Fernet key for Level 3 application encryption
    fernet_key = generate_fernet_key()
    print("1. Application Encryption Key (Fernet):")
    print(f"   Key: {fernet_key}")
    print(f"   Length: {len(fernet_key)} characters")
    
    # Generate database password
    db_password = generate_random_password(32)
    print(f"\n2. Database Password:")
    print(f"   Password: {db_password}")
    print(f"   Length: {len(db_password)} characters")
    
    # Generate Secrets Manager JSON for application keys
    app_keys_json = {
        "app_encryption_keys": {
            "level3_app_key_v1": fernet_key,
            "current_version": 1
        }
    }
    
    print(f"\n3. Secrets Manager JSON (pii-encryption-keys):")
    print(json.dumps(app_keys_json, indent=2))
    
    # Generate Secrets Manager JSON for database credentials
    db_credentials_json = {
        "username": "postgres",
        "password": db_password,
        "engine": "postgres",
        "host": "[RDS-ENDPOINT]",
        "port": 5432,
        "dbname": "pii_db"
    }
    
    print(f"\n4. Secrets Manager JSON (pii-database-credentials):")
    print(json.dumps(db_credentials_json, indent=2))
    
    # Validation
    print(f"\n5. Key Validation:")
    try:
        # Test Fernet key
        cipher = Fernet(fernet_key.encode())
        test_data = b"test encryption data"
        encrypted = cipher.encrypt(test_data)
        decrypted = cipher.decrypt(encrypted)
        assert decrypted == test_data
        print("   ✅ Fernet key validation successful")
    except Exception as e:
        print(f"   ❌ Fernet key validation failed: {e}")
    
    # Security recommendations
    print(f"\n6. Security Recommendations:")
    print("   - Store these keys securely in AWS Secrets Manager")
    print("   - Do not commit these keys to version control")
    print("   - Enable automatic rotation for the application keys")
    print("   - Use different keys for different environments")
    print("   - Monitor key usage through CloudTrail")
    
    # Next steps
    print(f"\n7. Next Steps:")
    print("   1. Copy the Secrets Manager JSON to AWS Console")
    print("   2. Create the secrets in AWS Secrets Manager")
    print("   3. Configure automatic rotation")
    print("   4. Update Lambda function with secret ARNs")
    print("   5. Test key retrieval from Lambda")

if __name__ == "__main__":
    main()