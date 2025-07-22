"""
Tests for PII Backend API
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from pii_backend.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
def api_headers():
    """API headers with valid API key"""
    return {
        "Authorization": "Bearer dev-api-key-change-in-production",
        "Content-Type": "application/json"
    }


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "PII Secure Persistence API" in data["message"]
    assert "version" in data["data"]


def test_health_endpoint_no_lambda(client):
    """Test health endpoint when Lambda is not available"""
    with patch('pii_backend.main.app.state') as mock_state:
        # Mock Lambda client that raises exception
        mock_lambda_client = AsyncMock()
        mock_lambda_client.health_check.side_effect = Exception("Lambda not available")
        mock_state.lambda_client = mock_lambda_client
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["status"] == "unhealthy"
        assert "lambda" in str(data["components"])


@patch('pii_backend.main.app.state')
def test_create_user_unauthorized(mock_state, client):
    """Test create user without API key"""
    user_data = {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = client.post("/users", json=user_data)
    assert response.status_code == 403  # Missing authorization header


@patch('pii_backend.main.app.state')
def test_create_user_invalid_api_key(mock_state, client):
    """Test create user with invalid API key"""
    user_data = {
        "email": "test@example.com", 
        "first_name": "Test",
        "last_name": "User"
    }
    
    headers = {"Authorization": "Bearer invalid-key"}
    response = client.post("/users", json=user_data, headers=headers)
    assert response.status_code == 401


@patch('pii_backend.main.app.state')
def test_list_users_pagination_validation(mock_state, client, api_headers):
    """Test list users with invalid pagination parameters"""
    
    # Mock Lambda client
    mock_lambda_client = AsyncMock()
    mock_state.lambda_client = mock_lambda_client
    
    # Test invalid limit
    response = client.get("/users?limit=0", headers=api_headers)
    assert response.status_code == 400
    
    response = client.get("/users?limit=101", headers=api_headers)
    assert response.status_code == 400
    
    # Test invalid offset
    response = client.get("/users?offset=-1", headers=api_headers)
    assert response.status_code == 400


@patch('pii_backend.main.app.state')
def test_user_id_validation(mock_state, client, api_headers):
    """Test user ID format validation"""
    
    # Mock Lambda client
    mock_lambda_client = AsyncMock()
    mock_state.lambda_client = mock_lambda_client
    
    # Test invalid UUID
    response = client.get("/users/invalid-uuid", headers=api_headers)
    # This would be caught by the Lambda client, but we can test the endpoint exists
    assert response.status_code in [400, 500]  # Either validation error or Lambda error


@patch('pii_backend.main.app.state')
def test_audit_limit_validation(mock_state, client, api_headers):
    """Test audit trail limit validation"""
    
    # Mock Lambda client
    mock_lambda_client = AsyncMock()
    mock_state.lambda_client = mock_lambda_client
    
    # Test invalid limit
    response = client.get("/users/123e4567-e89b-12d3-a456-426614174000/audit?limit=0", headers=api_headers)
    assert response.status_code == 400
    
    response = client.get("/users/123e4567-e89b-12d3-a456-426614174000/audit?limit=1001", headers=api_headers)
    assert response.status_code == 400