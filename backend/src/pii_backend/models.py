"""
Pydantic models for PII Backend API
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
import re


class UserCreateRequest(BaseModel):
    """Request model for creating a user"""
    
    # Level 1 fields (Low sensitivity)
    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(..., min_length=1, max_length=100, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="User's last name")
    phone: Optional[str] = Field(None, max_length=20, description="User's phone number")
    
    # Level 2 fields (Medium sensitivity)  
    address: Optional[str] = Field(None, max_length=500, description="User's address")
    date_of_birth: Optional[str] = Field(None, description="User's date of birth (YYYY-MM-DD)")
    ip_address: Optional[str] = Field(None, description="User's IP address")
    
    # Level 3 fields (High sensitivity)
    ssn: Optional[str] = Field(None, description="User's Social Security Number")
    bank_account: Optional[str] = Field(None, description="User's bank account number")
    credit_card: Optional[str] = Field(None, description="User's credit card number")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is not None:
            # Remove common phone formatting
            phone_digits = re.sub(r'[^\d]', '', v)
            if len(phone_digits) < 10 or len(phone_digits) > 15:
                raise ValueError('Phone number must be between 10-15 digits')
        return v
    
    @field_validator('date_of_birth')
    @classmethod
    def validate_date_of_birth(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Date of birth must be in YYYY-MM-DD format')
        return v
    
    @field_validator('ssn')
    @classmethod
    def validate_ssn(cls, v):
        if v is not None:
            # Remove common SSN formatting
            ssn_digits = re.sub(r'[^\d]', '', v)
            if len(ssn_digits) != 9:
                raise ValueError('SSN must be 9 digits')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1-555-0123",
                "address": "123 Main Street, Anytown, USA",
                "date_of_birth": "1990-01-01",
                "ssn": "123-45-6789",
                "bank_account": "1234567890"
            }
        }
    )


class UserData(BaseModel):
    """User data model for responses"""
    user_id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[str] = None
    ip_address: Optional[str] = None
    ssn: Optional[str] = None
    bank_account: Optional[str] = None
    credit_card: Optional[str] = None
    created_at: str


class UserCreated(BaseModel):
    """User creation response data"""
    user_id: str
    message: str
    processed_fields: int


class UserListItem(BaseModel):
    """User list item (basic info only)"""
    user_id: str
    email: str
    first_name: str
    last_name: str
    created_at: str


class UserListData(BaseModel):
    """User list response data"""
    users: List[UserListItem]
    total: int
    limit: int
    offset: int


class AuditLogEntry(BaseModel):
    """Audit log entry"""
    audit_id: str
    user_id: Optional[str] = None
    operation: str
    accessed_by: str
    success: bool
    error_message: Optional[str] = None
    timestamp: str


class AuditTrailData(BaseModel):
    """Audit trail response data"""
    audit_logs: List[AuditLogEntry]
    user_id: Optional[str] = None
    limit: int


class APIResponse(BaseModel):
    """Base API response model"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class UserResponse(APIResponse):
    """User operation response"""
    data: Optional[UserData] = None


class UserCreateResponse(APIResponse):
    """User creation response"""
    data: Optional[UserCreated] = None


class UserListResponse(APIResponse):
    """User list response"""
    data: Optional[UserListData] = None


class AuditTrailResponse(APIResponse):
    """Audit trail response"""
    data: Optional[AuditTrailData] = None


class HealthResponse(BaseModel):
    """Health check response"""
    success: bool
    status: str
    components: Dict[str, Any]
    timestamp: Optional[str] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())