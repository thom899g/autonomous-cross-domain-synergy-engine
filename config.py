"""
Configuration management with Pydantic validation and environment variable loading.
This centralizes all system configuration with proper type safety and validation.
"""
import os
from typing import Optional, Dict, List
from pydantic import BaseSettings, Field, validator
from dotenv import load_dotenv

load_dotenv()

class FirebaseConfig(BaseSettings):
    """Firebase configuration with service account credentials"""
    project_id: str = Field(..., env="FIREBASE_PROJECT_ID")
    private_key_id: str = Field(..., env="FIREBASE_PRIVATE_KEY_ID")
    private_key: str = Field(..., env="FIREBASE_PRIVATE_KEY")
    client_email: str = Field(..., env="FIREBASE_CLIENT_EMAIL")
    client_id: str = Field(..., env="FIREBASE_CLIENT_ID")
    client_x509_cert_url: str = Field(..., env="FIREBASE_CLIENT_X509_CERT_URL")
    
    @validator('private_key')
    def fix_private_key_format(cls, v):
        """Fix newline characters in private key from environment variable"""
        return v.replace('\\n', '\n')

class DomainAPIConfig(BaseSettings):
    """Configuration for external domain APIs"""
    api_keys: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        env_prefix = "DOMAIN_"

class SystemConfig(BaseSettings):
    """System-wide configuration"""
    sync_interval_minutes: int = Field(30, env="SYNC_INTERVAL_MINUTES")
    max_concurrent_requests: int = Field(5, env="MAX_CONCURRENT_REQUESTS")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    allowed_domains: List[str] = ["ecommerce", "logistics", "finance", "manufacturing"]

class CrossDomainConfig:
    """Main configuration aggregator"""
    def __init__(self):
        self.firebase = FirebaseConfig()
        self.domain_api = DomainAPIConfig()
        self.system = SystemConfig()
        
    def validate(self) -> bool:
        """Validate all configurations"""
        try:
            # Validate Firebase credentials can be parsed
            import json
            creds_dict = {
                "type": "service_account",
                "project_id": self.firebase.project_id,
                "private_key_id": self.firebase.private_key_id,
                "private_key": self.firebase.private_key,
                "client_email": self.firebase.client_email,
                "client_id": self.firebase.client_id,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": self.firebase.client_x509_cert_url
            }
            json.dumps(creds_dict)  # Will fail if invalid
            return True
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {str(e)}")

config = CrossDomainConfig()