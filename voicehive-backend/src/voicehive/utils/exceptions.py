"""Custom exceptions for VoiceHive application with enhanced error handling"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class VoiceHiveError(Exception):
    """Base exception for VoiceHive application with user-friendly messaging"""

    def __init__(
        self,
        message: str,
        user_message: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message  # Technical message for logs
        self.user_message = user_message or "An error occurred. Please try again."  # User-friendly message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause

    def get_user_message(self) -> str:
        """Get user-friendly error message"""
        return self.user_message

    def get_technical_message(self) -> str:
        """Get technical error message for logging"""
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.error_code,
            "message": self.user_message,  # Return user-friendly message in API
            "technical_message": self.message,  # Include technical details for debugging
            "details": self.details
        }


class AgentError(VoiceHiveError):
    """Exception raised by agent operations"""
    pass


class FunctionCallError(VoiceHiveError):
    """Exception raised during function calls"""
    pass


class OpenAIServiceError(VoiceHiveError):
    """Exception raised by OpenAI service"""
    pass


class AppointmentServiceError(VoiceHiveError):
    """Exception raised by appointment service"""
    pass


class LeadServiceError(VoiceHiveError):
    """Exception raised by lead service"""
    pass


class NotificationServiceError(VoiceHiveError):
    """Exception raised by notification service"""
    pass


class ValidationError(VoiceHiveError):
    """Exception raised for validation errors"""
    pass


class ConfigurationError(VoiceHiveError):
    """Exception raised for configuration errors"""
    pass


# Memory System Specific Exceptions
class MemoryError(VoiceHiveError):
    """Base exception for memory system operations"""
    pass


class MemoryConnectionError(MemoryError):
    """Exception raised when memory system connection fails"""
    pass


class MemoryStorageError(MemoryError):
    """Exception raised when memory storage operations fail"""
    pass


class MemoryRetrievalError(MemoryError):
    """Exception raised when memory retrieval operations fail"""
    pass


# Network and External Service Exceptions
class NetworkError(VoiceHiveError):
    """Exception raised for network-related errors"""
    pass


class ExternalServiceError(VoiceHiveError):
    """Exception raised when external services fail"""
    pass


class RateLimitError(ExternalServiceError):
    """Exception raised when rate limits are exceeded"""
    pass


class AuthenticationError(ExternalServiceError):
    """Exception raised for authentication failures"""
    pass


class TimeoutError(NetworkError):
    """Exception raised when operations timeout"""
    pass


# Data and Processing Exceptions
class DataValidationError(ValidationError):
    """Exception raised for data validation failures"""
    pass


class DataProcessingError(VoiceHiveError):
    """Exception raised during data processing operations"""
    pass


class SerializationError(DataProcessingError):
    """Exception raised during data serialization/deserialization"""
    pass


# Business Logic Exceptions
class BusinessLogicError(VoiceHiveError):
    """Exception raised for business logic violations"""
    pass


class ConflictError(BusinessLogicError):
    """Exception raised when conflicts occur (e.g., double booking)"""
    pass


class ResourceNotFoundError(VoiceHiveError):
    """Exception raised when requested resources are not found"""
    pass


class PermissionError(VoiceHiveError):
    """Exception raised for permission/authorization failures"""
    pass


# Retry Logic Support
class RetryableError(VoiceHiveError):
    """Base class for errors that should trigger retry logic"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, 
                 max_retries: int = 3, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after  # Seconds to wait before retry
        self.max_retries = max_retries


class TransientError(RetryableError):
    """Exception for temporary failures that should be retried"""
    pass


class ServiceUnavailableError(TransientError):
    """Exception raised when services are temporarily unavailable"""
    pass


# Error Handler Utility
class ErrorHandler:
    """Utility class for consistent error handling and logging"""
    
    @staticmethod
    def log_and_raise(exception_class: type, message: str, 
                     error_code: Optional[str] = None,
                     details: Optional[Dict[str, Any]] = None,
                     cause: Optional[Exception] = None,
                     log_level: str = "error") -> None:
        """Log error and raise exception"""
        
        # Create exception instance
        exc = exception_class(
            message=message,
            error_code=error_code,
            details=details,
            cause=cause
        )
        
        # Log the error
        log_message = f"{exception_class.__name__}: {message}"
        if details:
            log_message += f" | Details: {details}"
        if cause:
            log_message += f" | Caused by: {str(cause)}"
            
        getattr(logger, log_level)(log_message, exc_info=cause is not None)
        
        # Raise the exception
        raise exc
    
    @staticmethod
    def handle_external_service_error(service_name: str, operation: str, 
                                    original_error: Exception) -> None:
        """Handle errors from external services with appropriate classification"""
        
        error_message = str(original_error).lower()
        
        # Classify the error type
        if "timeout" in error_message or "timed out" in error_message:
            ErrorHandler.log_and_raise(
                TimeoutError,
                f"{service_name} {operation} timed out",
                error_code=f"{service_name.upper()}_TIMEOUT",
                details={"service": service_name, "operation": operation},
                cause=original_error
            )
        elif "rate limit" in error_message or "too many requests" in error_message:
            ErrorHandler.log_and_raise(
                RateLimitError,
                f"{service_name} rate limit exceeded during {operation}",
                error_code=f"{service_name.upper()}_RATE_LIMIT",
                details={"service": service_name, "operation": operation},
                cause=original_error
            )
        elif "unauthorized" in error_message or "authentication" in error_message:
            ErrorHandler.log_and_raise(
                AuthenticationError,
                f"{service_name} authentication failed during {operation}",
                error_code=f"{service_name.upper()}_AUTH_FAILED",
                details={"service": service_name, "operation": operation},
                cause=original_error
            )
        elif "connection" in error_message or "network" in error_message:
            ErrorHandler.log_and_raise(
                NetworkError,
                f"{service_name} network error during {operation}",
                error_code=f"{service_name.upper()}_NETWORK_ERROR",
                details={"service": service_name, "operation": operation},
                cause=original_error
            )
        else:
            # Generic external service error
            ErrorHandler.log_and_raise(
                ExternalServiceError,
                f"{service_name} error during {operation}: {str(original_error)}",
                error_code=f"{service_name.upper()}_ERROR",
                details={"service": service_name, "operation": operation},
                cause=original_error
            )
