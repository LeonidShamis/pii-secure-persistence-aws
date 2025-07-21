#!/usr/bin/env python3
"""
Generate a 32-byte Fernet key for PII encryption system.

This script generates a cryptographically secure Fernet key suitable for
application-layer encryption in the PII encryption system.
"""

from cryptography.fernet import Fernet


def generate_fernet_key() -> str:
    """Generate a new Fernet key and return it as a string."""
    key = Fernet.generate_key()
    return key.decode('utf-8')


def main():
    """Generate and print a new Fernet key."""
    key = generate_fernet_key()
    print(f"Generated 32-byte Fernet key: {key}")
    print("\nThis key should be used in AWS Secrets Manager for level3_app_key_v1")
    print("Keep this key secure and never commit it to version control!")


if __name__ == "__main__":
    main()