"""
PII Secure Persistence - FastAPI Backend
Main application entry point
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from dotenv import load_dotenv

from .config import settings
from .lambda_client import LambdaClient
from .models import (
    UserCreateRequest, 
    UserResponse, 
    UserListResponse, 
    AuditTrailResponse,
    HealthResponse,
    APIResponse
)
from .security import verify_api_key

# Load environment variables
load_dotenv()

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager"""
    # Startup
    print("🚀 PII Backend starting up...")
    print(f"Environment: {settings.environment}")
    print(f"Lambda Function: {settings.lambda_function_name}")
    
    # Initialize Lambda client
    app.state.lambda_client = LambdaClient()
    
    # Test Lambda connection
    try:
        health_check = await app.state.lambda_client.health_check()
        if health_check.get('success'):
            print("✅ Lambda connection healthy")
        else:
            print("⚠️ Lambda connection issues detected")
    except Exception as e:
        print(f"❌ Lambda connection failed: {e}")
    
    yield
    
    # Shutdown
    print("🛑 PII Backend shutting down...")

# Create FastAPI app
app = FastAPI(
    title="PII Secure Persistence API",
    description="Secure API for handling Personally Identifiable Information with three-tier encryption",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

def get_lambda_client() -> LambdaClient:
    """Dependency to get Lambda client"""
    return app.state.lambda_client

@app.get("/", response_model=APIResponse)
async def root():
    """Root endpoint"""
    return APIResponse(
        success=True,
        message="PII Secure Persistence API",
        data={
            "version": "1.0.0",
            "status": "healthy",
            "documentation": "/docs"
        }
    )

@app.get("/health", response_model=HealthResponse)
async def health_check(
    lambda_client: LambdaClient = Depends(get_lambda_client)
):
    """Health check endpoint"""
    try:
        # Check Lambda health
        lambda_health = await lambda_client.health_check()
        
        return HealthResponse(
            success=True,
            status="healthy",
            components={
                "backend": "healthy",
                "lambda": lambda_health.get('health', {})
            },
            timestamp=lambda_health.get('timestamp')
        )
    except Exception as e:
        return HealthResponse(
            success=False,
            status="unhealthy",
            components={
                "backend": "healthy",
                "lambda": f"error: {str(e)}"
            },
            error=str(e)
        )

@app.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreateRequest,
    lambda_client: LambdaClient = Depends(get_lambda_client),
    token: str = Depends(verify_api_key)
):
    """Create a new user with PII encryption"""
    try:
        result = await lambda_client.create_user(user_data.model_dump(exclude_unset=True))
        
        if result.get('success'):
            return UserResponse(
                success=True,
                message="User created successfully",
                data=result.get('result', {})
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Failed to create user')
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    lambda_client: LambdaClient = Depends(get_lambda_client),
    token: str = Depends(verify_api_key)
):
    """Get user by ID with PII decryption"""
    try:
        result = await lambda_client.get_user(user_id)
        
        if result.get('success'):
            return UserResponse(
                success=True,
                message="User retrieved successfully",
                data=result.get('result', {})
            )
        elif result.get('statusCode') == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Failed to retrieve user')
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user: {str(e)}"
        )

@app.get("/users", response_model=UserListResponse)
async def list_users(
    limit: int = 10,
    offset: int = 0,
    lambda_client: LambdaClient = Depends(get_lambda_client),
    token: str = Depends(verify_api_key)
):
    """List users (basic info only, no sensitive data)"""
    try:
        # Validate parameters
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )
        
        if offset < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Offset must be non-negative"
            )
        
        result = await lambda_client.list_users(limit=limit, offset=offset)
        
        if result.get('success'):
            return UserListResponse(
                success=True,
                message="Users listed successfully",
                data=result.get('result', {})
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Failed to list users')
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing users: {str(e)}"
        )

@app.get("/users/{user_id}/audit", response_model=AuditTrailResponse)
async def get_audit_trail(
    user_id: str,
    limit: int = 100,
    lambda_client: LambdaClient = Depends(get_lambda_client),
    token: str = Depends(verify_api_key)
):
    """Get audit trail for a user"""
    try:
        if limit < 1 or limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 1000"
            )
        
        result = await lambda_client.get_audit_trail(user_id=user_id, limit=limit)
        
        if result.get('success'):
            return AuditTrailResponse(
                success=True,
                message="Audit trail retrieved successfully",
                data=result.get('result', {})
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Failed to retrieve audit trail')
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving audit trail: {str(e)}"
        )

@app.get("/audit", response_model=AuditTrailResponse)
async def get_all_audit_logs(
    limit: int = 100,
    lambda_client: LambdaClient = Depends(get_lambda_client),
    token: str = Depends(verify_api_key)
):
    """Get audit trail for all users (admin only)"""
    try:
        if limit < 1 or limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 1000"
            )
        
        result = await lambda_client.get_audit_trail(limit=limit)
        
        if result.get('success'):
            return AuditTrailResponse(
                success=True,
                message="Audit trail retrieved successfully",
                data=result.get('result', {})
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Failed to retrieve audit trail')
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving audit trail: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "pii_backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )