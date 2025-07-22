"""
Security utilities for PII Backend
"""

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from .config import settings

security = HTTPBearer()


async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Verify API key from Authorization header
    
    In production, this should be replaced with:
    - JWT token validation
    - OAuth2 flow
    - API key database lookup
    - Rate limiting
    """
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Simple API key validation (replace in production)
    if credentials.credentials != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials


def validate_user_id(user_id: str) -> str:
    """Validate user ID format (UUID)"""
    import uuid
    
    try:
        # Validate UUID format
        uuid_obj = uuid.UUID(user_id)
        return str(uuid_obj)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format. Must be a valid UUID."
        )


def sanitize_input(data: str, max_length: int = 1000) -> str:
    """Basic input sanitization"""
    if not isinstance(data, str):
        return data
    
    # Remove null bytes and control characters
    sanitized = data.replace('\x00', '').replace('\r', '').replace('\n', ' ')
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


class SecurityHeaders:
    """Security headers middleware"""
    
    @staticmethod
    def get_security_headers() -> dict:
        """Get security headers for responses"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
        }