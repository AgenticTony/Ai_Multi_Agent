"""
Structured logging utilities for VoiceHive
Provides correlation IDs, structured JSON logging, and performance metrics
"""

import logging
import json
import time
import uuid
from typing import Dict, Any, Optional
from contextvars import ContextVar
from functools import wraps
from datetime import datetime

# Context variable for correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        
        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if available
        corr_id = correlation_id.get()
        if corr_id:
            log_entry["correlation_id"] = corr_id
        
        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add stack trace if present
        if record.stack_info:
            log_entry["stack_trace"] = record.stack_info
        
        return json.dumps(log_entry, ensure_ascii=False)


class CorrelationIdFilter(logging.Filter):
    """
    Filter that adds correlation ID to log records
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to record if available"""
        corr_id = correlation_id.get()
        if corr_id:
            record.correlation_id = corr_id
        return True


def setup_logging(log_level: str = "INFO", use_json: bool = True) -> None:
    """
    Setup structured logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Whether to use JSON formatting
    """
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    
    if use_json:
        # Use structured JSON formatter
        formatter = StructuredFormatter()
    else:
        # Use standard formatter for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    console_handler.addFilter(CorrelationIdFilter())
    
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with structured logging capabilities
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_with_context(logger: logging.Logger, level: str, message: str, **kwargs) -> None:
    """
    Log a message with additional context fields
    
    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **kwargs: Additional context fields
    """
    
    # Create log record
    log_method = getattr(logger, level.lower())
    
    # Add extra fields to record
    extra = {"extra_fields": kwargs}
    log_method(message, extra=extra)


def set_correlation_id(corr_id: Optional[str] = None) -> str:
    """
    Set correlation ID for current context
    
    Args:
        corr_id: Correlation ID to set (generates new one if None)
        
    Returns:
        The correlation ID that was set
    """
    if corr_id is None:
        corr_id = str(uuid.uuid4())
    
    correlation_id.set(corr_id)
    return corr_id


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID
    
    Returns:
        Current correlation ID or None if not set
    """
    return correlation_id.get()


def performance_logger(func_name: Optional[str] = None):
    """
    Decorator to log function performance metrics
    
    Args:
        func_name: Custom function name for logging (uses actual name if None)
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            name = func_name or func.__name__
            
            start_time = time.time()
            
            try:
                log_with_context(
                    logger, "debug", f"Starting {name}",
                    function=name,
                    event="function_start"
                )
                
                result = await func(*args, **kwargs)
                
                duration = time.time() - start_time
                log_with_context(
                    logger, "info", f"Completed {name}",
                    function=name,
                    event="function_complete",
                    duration_ms=round(duration * 1000, 2),
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                log_with_context(
                    logger, "error", f"Failed {name}: {str(e)}",
                    function=name,
                    event="function_error",
                    duration_ms=round(duration * 1000, 2),
                    success=False,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            name = func_name or func.__name__
            
            start_time = time.time()
            
            try:
                log_with_context(
                    logger, "debug", f"Starting {name}",
                    function=name,
                    event="function_start"
                )
                
                result = func(*args, **kwargs)
                
                duration = time.time() - start_time
                log_with_context(
                    logger, "info", f"Completed {name}",
                    function=name,
                    event="function_complete",
                    duration_ms=round(duration * 1000, 2),
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                log_with_context(
                    logger, "error", f"Failed {name}: {str(e)}",
                    function=name,
                    event="function_error",
                    duration_ms=round(duration * 1000, 2),
                    success=False,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class RequestLogger:
    """
    Context manager for request-level logging
    """
    
    def __init__(self, request_id: Optional[str] = None, **context):
        self.request_id = request_id or str(uuid.uuid4())
        self.context = context
        self.start_time = None
        self.logger = get_logger("voicehive.request")
    
    def __enter__(self):
        """Start request logging context"""
        set_correlation_id(self.request_id)
        self.start_time = time.time()
        
        log_with_context(
            self.logger, "info", "Request started",
            event="request_start",
            request_id=self.request_id,
            **self.context
        )
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End request logging context"""
        duration = time.time() - self.start_time if self.start_time else 0
        
        if exc_type is None:
            log_with_context(
                self.logger, "info", "Request completed",
                event="request_complete",
                request_id=self.request_id,
                duration_ms=round(duration * 1000, 2),
                success=True,
                **self.context
            )
        else:
            log_with_context(
                self.logger, "error", f"Request failed: {exc_val}",
                event="request_error",
                request_id=self.request_id,
                duration_ms=round(duration * 1000, 2),
                success=False,
                error_type=exc_type.__name__ if exc_type else None,
                error_message=str(exc_val) if exc_val else None,
                **self.context
            )


# Convenience functions for common logging patterns
def log_api_request(method: str, path: str, status_code: int, duration_ms: float, **kwargs):
    """Log API request with standard fields"""
    logger = get_logger("voicehive.api")
    
    log_with_context(
        logger, "info", f"{method} {path} - {status_code}",
        event="api_request",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
        **kwargs
    )


def log_external_api_call(service: str, endpoint: str, status_code: int, duration_ms: float, **kwargs):
    """Log external API call with standard fields"""
    logger = get_logger("voicehive.external")
    
    log_with_context(
        logger, "info", f"External API call to {service}",
        event="external_api_call",
        service=service,
        endpoint=endpoint,
        status_code=status_code,
        duration_ms=duration_ms,
        **kwargs
    )


def log_function_call(function_name: str, parameters: Dict[str, Any], result: Dict[str, Any], **kwargs):
    """Log AI function call with standard fields"""
    logger = get_logger("voicehive.function_call")
    
    log_with_context(
        logger, "info", f"Function call: {function_name}",
        event="function_call",
        function_name=function_name,
        parameters=parameters,
        result=result,
        **kwargs
    )


def log_conversation_event(call_id: str, event_type: str, message: str, **kwargs):
    """Log conversation event with standard fields"""
    logger = get_logger("voicehive.conversation")
    
    log_with_context(
        logger, "info", f"Conversation event: {event_type}",
        event="conversation_event",
        call_id=call_id,
        event_type=event_type,
        message=message,
        **kwargs
    )
