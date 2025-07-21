# Infrastructure

This directory contains AWS infrastructure setup tools and configuration for the PII Encryption System prototype.

## Overview

This infrastructure package provides tools and guides for setting up the AWS security infrastructure required for the PII encryption system, including KMS keys, Secrets Manager, and IAM roles.

## Contents

- **`aws-console-setup-guide.md`** - Step-by-step AWS Console setup guide for manual resource creation
- **`generate-keys.py`** - Comprehensive key generation script for Fernet keys, database passwords, and Secrets Manager JSON
- **`kms-setup.tf`** - Terraform configuration for KMS keys and related resources
- **`iam-policies.json`** - IAM policy definitions for the encryption system
- **`generate_fernet_key.py`** - Simple Fernet key generation script

## Quick Start

### Generate Encryption Keys

Generate all required keys for the PII encryption system:

```bash
uv run generate-keys.py
```

This script generates:
- Fernet key for Level 3 application-layer encryption
- Secure database password
- Complete Secrets Manager JSON configurations

### Manual AWS Setup

Follow the comprehensive setup guide:

```bash
# Open the manual setup guide
cat aws-console-setup-guide.md
```

The guide covers:
- KMS key creation (Level 2, Level 3, RDS encryption)
- Secrets Manager configuration
- IAM roles and policies
- Security verification steps

## Dependencies

This is a standalone `uv` project with the following dependencies:
- `cryptography` - For Fernet key generation

## Security Notes

- Never commit generated keys to version control
- Use generated keys immediately in AWS Secrets Manager
- Follow the principle of least privilege for IAM roles
- Enable automatic key rotation for all KMS keys

## Related Documentation

- Main project documentation: `../docs/`
- Architecture overview: `../docs/architecture.md`
- Implementation plan: `../docs/implementation-plan.md`