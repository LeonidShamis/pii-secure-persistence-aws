"""
Configuration management for PII Backend
"""

import os
from typing import List, Optional, Union
from pydantic import ConfigDict, field_validator
from pydantic_settings import BaseSettings
import json


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    environment: str = "development"
    debug: bool = True
    api_title: str = "PII Secure Persistence API"
    api_version: str = "1.0.0"
    
    # API Security
    api_key: str = "dev-api-key-change-in-production"
    allowed_origins: Union[List[str], str] = ["*"]  # Allow all origins for prototype - restrict in production!
    
    @field_validator('allowed_origins')
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse allowed_origins from string or list"""
        if isinstance(v, str):
            # Handle special case for wildcard
            if v == "*":
                return ["*"]
            # Try to parse as JSON
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                else:
                    return [str(parsed)]
            except json.JSONDecodeError:
                # If not valid JSON, treat as single origin
                return [v]
        return v
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    lambda_function_name: str = "pii-encryption-handler"
    
    # Lambda Client Configuration
    lambda_timeout: int = 30  # seconds
    lambda_retry_attempts: int = 3
    
    # Logging
    log_level: str = "INFO"
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="PII_",
        extra="ignore"  # Ignore extra environment variables
    )


# Global settings instance
settings = Settings()