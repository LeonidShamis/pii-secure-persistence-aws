#!/usr/bin/env python3
"""
Test script for PII Encryption Lambda Function

This script provides unit tests and integration tests for the Lambda function.
Note: Integration tests require AWS credentials and actual AWS resources.
"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pii_encryption_lambda.lambda_function import (
    PIIClassifier, 
    EncryptionHandler,
    lambda_handler
)
from pii_encryption_lambda.database_operations import DatabaseManager


class TestPIIClassifier(unittest.TestCase):
    """Test PII classification logic"""
    
    def test_level_1_classification(self):
        """Test Level 1 (low sensitivity) field classification"""
        level_1_fields = ['email', 'first_name', 'last_name', 'phone']
        
        for field in level_1_fields:
            with self.subTest(field=field):
                level = PIIClassifier.classify_pii_level(field)
                self.assertEqual(level, 1, f"Field {field} should be Level 1")
    
    def test_level_2_classification(self):
        """Test Level 2 (medium sensitivity) field classification"""
        level_2_fields = ['address', 'date_of_birth', 'dob', 'ip_address']
        
        for field in level_2_fields:
            with self.subTest(field=field):
                level = PIIClassifier.classify_pii_level(field)
                self.assertEqual(level, 2, f"Field {field} should be Level 2")
    
    def test_level_3_classification(self):
        """Test Level 3 (high sensitivity) field classification"""
        level_3_fields = ['ssn', 'bank_account', 'credit_card', 'medical_record']
        
        for field in level_3_fields:
            with self.subTest(field=field):
                level = PIIClassifier.classify_pii_level(field)
                self.assertEqual(level, 3, f"Field {field} should be Level 3")
    
    def test_unknown_field_defaults_to_level_1(self):
        """Test that unknown fields default to Level 1"""
        unknown_fields = ['unknown_field', 'random_data', 'test_field']
        
        for field in unknown_fields:
            with self.subTest(field=field):
                level = PIIClassifier.classify_pii_level(field)
                self.assertEqual(level, 1, f"Unknown field {field} should default to Level 1")
    
    def test_case_insensitive_classification(self):
        """Test that classification is case insensitive"""
        test_cases = [
            ('EMAIL', 1),
            ('Address', 2),
            ('SSN', 3),
            ('First_Name', 1),
            ('CREDIT_CARD', 3)
        ]
        
        for field, expected_level in test_cases:
            with self.subTest(field=field):
                level = PIIClassifier.classify_pii_level(field)
                self.assertEqual(level, expected_level)
    
    def test_get_encryption_requirements(self):
        """Test encryption requirements generation"""
        test_cases = [
            ('email', {'level': 1, 'requires_kms': False, 'requires_app_encryption': False}),
            ('address', {'level': 2, 'requires_kms': True, 'requires_app_encryption': False}),
            ('ssn', {'level': 3, 'requires_kms': True, 'requires_app_encryption': True})
        ]
        
        for field, expected in test_cases:
            with self.subTest(field=field):
                requirements = PIIClassifier.get_encryption_requirements(field)
                for key, value in expected.items():
                    self.assertEqual(requirements[key], value)


class TestEncryptionHandler(unittest.TestCase):
    """Test encryption handler functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.handler = EncryptionHandler()
    
    @patch('boto3.client')
    def test_initialization(self, mock_boto3):
        """Test EncryptionHandler initialization"""
        handler = EncryptionHandler()
        self.assertIsNotNone(handler.kms)
        self.assertIsNotNone(handler.secrets)
        self.assertEqual(handler.level2_kms_alias, 'alias/pii-level2')
        self.assertEqual(handler.level3_kms_alias, 'alias/pii-level3')
    
    @patch.object(EncryptionHandler, 'get_app_keys')
    def test_get_current_app_cipher(self, mock_get_keys):
        """Test getting current application cipher"""
        # Generate a valid Fernet key (32 bytes, base64 encoded)
        from cryptography.fernet import Fernet
        valid_key = Fernet.generate_key().decode()
        
        mock_get_keys.return_value = {
            'current_version': 1,
            'level3_app_key_v1': valid_key
        }
        
        cipher = self.handler.get_current_app_cipher()
        self.assertIsNotNone(cipher)
    
    def test_encrypt_field_level_1(self):
        """Test Level 1 field encryption (pass-through)"""
        result = self.handler.encrypt_field('email', 'test@example.com')
        
        self.assertEqual(result['value'], 'test@example.com')
        self.assertEqual(result['level'], 1)
        self.assertFalse(result['encrypted'])
        self.assertEqual(result['method'], 'rds_only')
    
    @patch('boto3.client')
    def test_encrypt_field_level_2(self, mock_boto3):
        """Test Level 2 field encryption (KMS only)"""
        # Mock KMS client
        mock_kms = Mock()
        mock_kms.encrypt.return_value = {
            'CiphertextBlob': b'encrypted_data_mock'
        }
        
        # Mock Secrets client
        mock_secrets = Mock()
        
        # Configure boto3.client to return appropriate mocks
        def mock_client_side_effect(service_name, **kwargs):
            if service_name == 'kms':
                return mock_kms
            elif service_name == 'secretsmanager':
                return mock_secrets
            return Mock()
        
        mock_boto3.side_effect = mock_client_side_effect
        
        # Create handler with mocked clients
        handler = EncryptionHandler()
        result = handler.encrypt_field('address', '123 Main St')
        
        self.assertEqual(result['level'], 2)
        self.assertTrue(result['encrypted'])
        self.assertEqual(result['method'], 'kms_only')
        self.assertIsNotNone(result['value'])
    
    def test_encrypt_field_empty_value(self):
        """Test encryption of empty/null values"""
        result = self.handler.encrypt_field('email', None)
        
        self.assertIsNone(result['value'])
        self.assertFalse(result['encrypted'])
    
    def test_decrypt_field_level_1(self):
        """Test Level 1 field decryption (pass-through)"""
        result = self.handler.decrypt_field('email', 'test@example.com')
        self.assertEqual(result, 'test@example.com')


class TestLambdaHandler(unittest.TestCase):
    """Test Lambda handler functionality"""
    
    @patch('pii_encryption_lambda.lambda_function.EncryptionHandler')
    @patch('pii_encryption_lambda.lambda_function.DatabaseManager')
    def test_lambda_handler_health_check(self, mock_db_manager, mock_handler):
        """Test health check operation"""
        # Mock the health check response
        mock_handler_instance = Mock()
        mock_db_manager_instance = Mock()
        mock_handler.return_value = mock_handler_instance
        mock_db_manager.return_value = mock_db_manager_instance
        
        # Mock health check components
        mock_handler_instance.kms.describe_key.return_value = {}
        mock_handler_instance.get_app_keys.return_value = {}
        mock_handler_instance.get_db_connection.return_value = Mock()
        mock_db_manager_instance.validate_database_schema.return_value = {'overall': True}
        
        event = {'operation': 'health'}
        context = {}
        
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertTrue(body['success'])
        self.assertIn('health', body)
    
    @patch('pii_encryption_lambda.lambda_function.EncryptionHandler')
    @patch('pii_encryption_lambda.lambda_function.DatabaseManager')
    def test_lambda_handler_create_user(self, mock_db_manager, mock_handler):
        """Test create user operation"""
        # Setup mocks
        mock_handler_instance = Mock()
        mock_db_manager_instance = Mock()
        mock_handler.return_value = mock_handler_instance
        mock_db_manager.return_value = mock_db_manager_instance
        
        # Mock encryption results
        mock_handler_instance.encrypt_field.side_effect = [
            {'value': 'test@example.com', 'level': 1, 'encrypted': False, 'method': 'rds_only'},
            {'value': 'encrypted_address', 'level': 2, 'encrypted': True, 'method': 'kms_only', 'kms_key': 'alias/pii-level2'},
            {'value': 'double_encrypted_ssn', 'level': 3, 'encrypted': True, 'method': 'double_encryption', 'app_key_version': 1, 'kms_key': 'alias/pii-level3'}
        ]
        
        mock_db_manager_instance.store_encrypted_user.return_value = 'test-user-id'
        mock_handler_instance.log_audit = Mock()
        
        event = {
            'operation': 'create_user',
            'data': {
                'email': 'test@example.com',
                'address': '123 Main St',
                'ssn': '123-45-6789'
            }
        }
        context = {}
        
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertTrue(body['success'])
        self.assertEqual(body['user_id'], 'test-user-id')
        self.assertEqual(body['processed_fields'], 3)
    
    def test_lambda_handler_invalid_operation(self):
        """Test Lambda handler with invalid operation"""
        event = {'operation': 'invalid_operation'}
        context = {}
        
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertFalse(body['success'])
        self.assertIn('error', body)
    
    def test_lambda_handler_missing_operation(self):
        """Test Lambda handler with missing operation"""
        event = {}
        context = {}
        
        response = lambda_handler(event, context)
        
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertFalse(body['success'])
        self.assertIn('error', body)


class TestIntegration(unittest.TestCase):
    """Integration tests (require AWS credentials and resources)"""
    
    def setUp(self):
        """Skip integration tests if AWS credentials not available"""
        try:
            import boto3
            # Try to create a client to test credentials
            boto3.client('sts').get_caller_identity()
            self.skip_integration = False
        except Exception:
            self.skip_integration = True
    
    def test_end_to_end_user_lifecycle(self):
        """Test complete user lifecycle: create -> retrieve -> delete"""
        if self.skip_integration:
            self.skipTest("AWS credentials not available")
        
        # This would test the complete flow with real AWS resources
        # Implementation would depend on having test AWS environment
        pass


def create_test_events():
    """Create sample test events for manual testing"""
    events = {
        'health_check': {
            'operation': 'health'
        },
        'create_user': {
            'operation': 'create_user',
            'data': {
                'email': 'john.doe@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'address': '123 Main Street, Anytown, USA',
                'date_of_birth': '1990-01-01',
                'ssn': '123-45-6789',
                'bank_account': '1234567890'
            }
        },
        'get_user': {
            'operation': 'get_user',
            'user_id': 'test-user-id'
        },
        'list_users': {
            'operation': 'list_users',
            'limit': 10,
            'offset': 0
        },
        'audit_trail': {
            'operation': 'audit_trail',
            'user_id': 'test-user-id',
            'limit': 50
        }
    }
    
    return events


def main():
    """Run tests or generate test events"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test PII Encryption Lambda")
    parser.add_argument("--generate-events", action="store_true",
                       help="Generate sample test events")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose test output")
    
    args = parser.parse_args()
    
    if args.generate_events:
        events = create_test_events()
        events_dir = os.path.join(os.path.dirname(__file__), 'test_events')
        os.makedirs(events_dir, exist_ok=True)
        
        for event_name, event_data in events.items():
            with open(os.path.join(events_dir, f'{event_name}.json'), 'w') as f:
                json.dump(event_data, f, indent=2)
        
        print(f"Test events generated in {events_dir}/")
        return
    
    # Run unit tests
    verbosity = 2 if args.verbose else 1
    unittest.main(argv=[''], verbosity=verbosity, exit=False)


if __name__ == "__main__":
    main()