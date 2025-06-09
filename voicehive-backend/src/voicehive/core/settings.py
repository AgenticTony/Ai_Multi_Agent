import logging
from enum import Enum
from typing import Optional, Dict, Any, List

from pydantic import Field, validator, model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """Application settings with enhanced validation and configuration management"""
    
    # Application Configuration
    app_name: str = Field(default="VoiceHive Backend", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    port: int = Field(default=8000, env="PORT", ge=1, le=65535)
    log_level: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Security Configuration
    secret_key: str = Field(..., env="SECRET_KEY", min_length=32)
    allowed_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0"],
        env="ALLOWED_HOSTS"
    )
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY", min_length=20)
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=150, env="OPENAI_MAX_TOKENS", ge=1, le=4000)
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE", ge=0.0, le=2.0)
    openai_timeout: int = Field(default=30, env="OPENAI_TIMEOUT", ge=1, le=300)
    openai_max_retries: int = Field(default=3, env="OPENAI_MAX_RETRIES", ge=1, le=10)
    
    # Vapi.ai Configuration
    vapi_api_key: str = Field(..., env="VAPI_API_KEY", min_length=10)
    vapi_phone_number: Optional[str] = Field(default=None, env="VAPI_PHONE_NUMBER")
    vapi_webhook_secret: Optional[str] = Field(default=None, env="VAPI_WEBHOOK_SECRET")
    
    # Google Cloud Configuration
    google_cloud_project: Optional[str] = Field(default=None, env="GOOGLE_CLOUD_PROJECT")
    google_application_credentials: Optional[str] = Field(default=None, env="GOOGLE_APPLICATION_CREDENTIALS")
    
    # Mem0 Configuration
    mem0_api_key: Optional[str] = Field(default=None, env="MEM0_API_KEY")
    mem0_timeout: int = Field(default=30, env="MEM0_TIMEOUT", ge=1, le=300)
    mem0_max_retries: int = Field(default=3, env="MEM0_MAX_RETRIES", ge=1, le=10)
    mem0_batch_size: int = Field(default=10, env="MEM0_BATCH_SIZE", ge=1, le=100)
    
    # Twilio Configuration
    twilio_account_sid: Optional[str] = Field(default=None, env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(default=None, env="TWILIO_AUTH_TOKEN")
    twilio_phone_number: Optional[str] = Field(default=None, env="TWILIO_PHONE_NUMBER")
    twilio_timeout: int = Field(default=30, env="TWILIO_TIMEOUT", ge=1, le=300)
    
    # Email Configuration
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT", ge=1, le=65535)
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")
    smtp_timeout: int = Field(default=30, env="SMTP_TIMEOUT", ge=1, le=300)
    
    # Firebase Configuration
    firebase_project_id: Optional[str] = Field(default=None, env="FIREBASE_PROJECT_ID")
    firebase_private_key_id: Optional[str] = Field(default=None, env="FIREBASE_PRIVATE_KEY_ID")
    firebase_private_key: Optional[str] = Field(default=None, env="FIREBASE_PRIVATE_KEY")
    firebase_client_email: Optional[str] = Field(default=None, env="FIREBASE_CLIENT_EMAIL")
    firebase_client_id: Optional[str] = Field(default=None, env="FIREBASE_CLIENT_ID")
    
    # Agent Configuration
    conversation_history_limit: int = Field(default=10, env="CONVERSATION_HISTORY_LIMIT", ge=1, le=100)
    response_timeout: int = Field(default=30, env="RESPONSE_TIMEOUT", ge=1, le=300)
    max_function_calls: int = Field(default=5, env="MAX_FUNCTION_CALLS", ge=1, le=20)
    agent_system_prompt_max_length: int = Field(default=2000, env="AGENT_SYSTEM_PROMPT_MAX_LENGTH", ge=100)
    
    # Performance Configuration
    cache_ttl: int = Field(default=300, env="CACHE_TTL", ge=1, le=86400)  # 5 minutes default
    cache_max_size: int = Field(default=1000, env="CACHE_MAX_SIZE", ge=1, le=10000)
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT", ge=1, le=300)
    
    # Retry Configuration
    default_max_retries: int = Field(default=3, env="DEFAULT_MAX_RETRIES", ge=1, le=10)
    default_retry_delay: float = Field(default=1.0, env="DEFAULT_RETRY_DELAY", ge=0.1, le=60.0)
    default_max_retry_delay: float = Field(default=60.0, env="DEFAULT_MAX_RETRY_DELAY", ge=1.0, le=300.0)
    
    # Database Configuration (for future use)
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    database_pool_size: int = Field(default=5, env="DATABASE_POOL_SIZE", ge=1, le=50)
    database_timeout: int = Field(default=30, env="DATABASE_TIMEOUT", ge=1, le=300)
    
    # Monitoring Configuration
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT", ge=1, le=65535)
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL", ge=1, le=3600)
    
    # Rate Limiting Configuration
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS", ge=1, le=10000)
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW", ge=1, le=3600)
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    @validator('allowed_hosts', pre=True)
    def parse_allowed_hosts(cls, v):
        """Parse allowed hosts from string or list"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(',') if host.strip()]
        return v
    
    @validator('firebase_private_key', pre=True)
    def parse_firebase_private_key(cls, v):
        """Parse Firebase private key, handling escaped newlines"""
        if v:
            return v.replace('\\n', '\n')
        return v
    
    @model_validator(mode='after')
    def validate_environment_specific_settings(self):
        """Validate settings based on environment"""
        environment = self.environment

        if environment == Environment.PRODUCTION:
            # Production-specific validations
            if self.debug:
                logger.warning("Debug mode is enabled in production environment")

            if self.log_level == LogLevel.DEBUG:
                logger.warning("Debug logging is enabled in production environment")

            # Ensure critical services are configured in production
            required_prod_settings = [
                ('secret_key', self.secret_key),
                ('openai_api_key', self.openai_api_key),
                ('vapi_api_key', self.vapi_api_key)
            ]

            for setting_name, setting_value in required_prod_settings:
                if not setting_value:
                    raise ValueError(f"{setting_name} is required in production environment")

        # Validate service dependencies
        if self.twilio_account_sid and not self.twilio_auth_token:
            raise ValueError("twilio_auth_token is required when twilio_account_sid is provided")

        if self.smtp_host and not self.smtp_username:
            logger.warning("SMTP host configured but no username provided")

        return self
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment"""
        return self.environment == Environment.TESTING
    
    @property
    def ENVIRONMENT(self) -> str:
        """Get environment as string for compatibility"""
        return self.environment.value
    
    @property
    def DEBUG(self) -> bool:
        """Get debug flag for compatibility"""
        return self.debug
    
    @property
    def ALLOWED_HOSTS(self) -> List[str]:
        """Get allowed hosts for compatibility"""
        return self.allowed_hosts
    
    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Get CORS origins for compatibility"""
        return self.cors_origins
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration dictionary"""
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model,
            "max_tokens": self.openai_max_tokens,
            "temperature": self.openai_temperature,
            "timeout": self.openai_timeout,
            "max_retries": self.openai_max_retries
        }
    
    def get_mem0_config(self) -> Dict[str, Any]:
        """Get Mem0 configuration dictionary"""
        return {
            "api_key": self.mem0_api_key,
            "timeout": self.mem0_timeout,
            "max_retries": self.mem0_max_retries,
            "batch_size": self.mem0_batch_size
        }
    
    def get_twilio_config(self) -> Dict[str, Any]:
        """Get Twilio configuration dictionary"""
        return {
            "account_sid": self.twilio_account_sid,
            "auth_token": self.twilio_auth_token,
            "phone_number": self.twilio_phone_number,
            "timeout": self.twilio_timeout
        }
    
    def get_smtp_config(self) -> Dict[str, Any]:
        """Get SMTP configuration dictionary"""
        return {
            "host": self.smtp_host,
            "port": self.smtp_port,
            "username": self.smtp_username,
            "password": self.smtp_password,
            "use_tls": self.smtp_use_tls,
            "timeout": self.smtp_timeout
        }
    
    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry configuration dictionary"""
        return {
            "max_retries": self.default_max_retries,
            "base_delay": self.default_retry_delay,
            "max_delay": self.default_max_retry_delay
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache configuration dictionary"""
        return {
            "ttl": self.cache_ttl,
            "max_size": self.cache_max_size
        }
    
    def validate_required_services(self) -> Dict[str, bool]:
        """Validate which services are properly configured"""
        return {
            "openai": bool(self.openai_api_key),
            "vapi": bool(self.vapi_api_key),
            "mem0": bool(self.mem0_api_key),
            "twilio": bool(self.twilio_account_sid and self.twilio_auth_token),
            "smtp": bool(self.smtp_host and self.smtp_username),
            "firebase": bool(self.firebase_project_id and self.firebase_private_key),
            "google_cloud": bool(self.google_cloud_project)
        }
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        validate_assignment = True
        extra = "forbid"  # Prevent extra fields


# Global settings instance
settings = Settings()


# Configuration validation on startup
def validate_configuration():
    """Validate configuration on application startup"""
    try:
        logger.info(f"Starting {settings.app_name} v{settings.version}")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Log level: {settings.log_level}")
        
        # Validate required services
        service_status = settings.validate_required_services()
        
        logger.info("Service configuration status:")
        for service, configured in service_status.items():
            status = "✓ Configured" if configured else "✗ Not configured"
            logger.info(f"  {service}: {status}")
        
        # Warn about missing optional services
        if not service_status["mem0"]:
            logger.warning("Mem0 not configured - using fallback memory storage")
        
        if not service_status["twilio"]:
            logger.warning("Twilio not configured - SMS notifications disabled")
        
        if not service_status["smtp"]:
            logger.warning("SMTP not configured - email notifications disabled")
        
        logger.info("Configuration validation completed successfully")
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        raise


def get_settings() -> Settings:
    """Get the global settings instance"""
    return settings


# Validate configuration when module is imported
if not settings.is_testing:
    validate_configuration()
