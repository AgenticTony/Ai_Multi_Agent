"""Retry logic utilities for handling transient failures"""

import asyncio
import logging
import time
from functools import wraps
from typing import Callable, Type, Union, Tuple, Optional, Any
from .exceptions import RetryableError, TransientError, RateLimitError, TimeoutError, NetworkError

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Tuple[Type[Exception], ...] = (
            TransientError,
            RateLimitError,
            TimeoutError,
            NetworkError,
            ConnectionError,
        )
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions


class RetryHandler:
    """Handles retry logic for operations"""
    
    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()
    
    def calculate_delay(self, attempt: int, retry_after: Optional[int] = None) -> float:
        """Calculate delay before next retry attempt"""
        
        if retry_after is not None:
            # Use server-specified retry delay (e.g., from rate limiting)
            return min(retry_after, self.config.max_delay)
        
        # Exponential backoff with jitter
        delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))
        
        if self.config.jitter:
            # Add jitter to prevent thundering herd
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return min(delay, self.config.max_delay)
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if an exception should trigger a retry"""
        
        # Check if we've exceeded max attempts
        if attempt >= self.config.max_attempts:
            return False
        
        # Check if exception is retryable
        if not isinstance(exception, self.config.retryable_exceptions):
            return False
        
        # Check if it's a RetryableError with custom max_retries
        if isinstance(exception, RetryableError):
            return attempt < exception.max_retries
        
        return True
    
    async def execute_with_retry(
        self,
        operation: Callable,
        *args,
        operation_name: str = "operation",
        **kwargs
    ) -> Any:
        """Execute an async operation with retry logic"""
        
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                logger.debug(f"Executing {operation_name}, attempt {attempt}/{self.config.max_attempts}")
                
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(*args, **kwargs)
                else:
                    result = operation(*args, **kwargs)
                
                if attempt > 1:
                    logger.info(f"{operation_name} succeeded on attempt {attempt}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    logger.error(f"{operation_name} failed permanently after {attempt} attempts: {str(e)}")
                    raise e
                
                # Calculate delay
                retry_after = getattr(e, 'retry_after', None)
                delay = self.calculate_delay(attempt, retry_after)
                
                logger.warning(
                    f"{operation_name} failed on attempt {attempt}/{self.config.max_attempts}: {str(e)}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                
                await asyncio.sleep(delay)
        
        # If we get here, all retries failed
        logger.error(f"{operation_name} failed after {self.config.max_attempts} attempts")
        raise last_exception
    
    def execute_sync_with_retry(
        self,
        operation: Callable,
        *args,
        operation_name: str = "operation",
        **kwargs
    ) -> Any:
        """Execute a synchronous operation with retry logic"""
        
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                logger.debug(f"Executing {operation_name}, attempt {attempt}/{self.config.max_attempts}")
                
                result = operation(*args, **kwargs)
                
                if attempt > 1:
                    logger.info(f"{operation_name} succeeded on attempt {attempt}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                if not self.should_retry(e, attempt):
                    logger.error(f"{operation_name} failed permanently after {attempt} attempts: {str(e)}")
                    raise e
                
                # Calculate delay
                retry_after = getattr(e, 'retry_after', None)
                delay = self.calculate_delay(attempt, retry_after)
                
                logger.warning(
                    f"{operation_name} failed on attempt {attempt}/{self.config.max_attempts}: {str(e)}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                
                time.sleep(delay)
        
        # If we get here, all retries failed
        logger.error(f"{operation_name} failed after {self.config.max_attempts} attempts")
        raise last_exception


# Decorator for automatic retry
def retry_on_failure(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        TransientError,
        RateLimitError,
        TimeoutError,
        NetworkError,
        ConnectionError,
    ),
    operation_name: Optional[str] = None
):
    """Decorator to add retry logic to functions"""
    
    def decorator(func: Callable) -> Callable:
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay,
            exponential_base=exponential_base,
            jitter=jitter,
            retryable_exceptions=retryable_exceptions
        )
        
        retry_handler = RetryHandler(config)
        func_name = operation_name or func.__name__
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                return await retry_handler.execute_with_retry(
                    func, *args, operation_name=func_name, **kwargs
                )
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return retry_handler.execute_sync_with_retry(
                    func, *args, operation_name=func_name, **kwargs
                )
            return sync_wrapper
    
    return decorator


# Global retry handler instance
default_retry_handler = RetryHandler()


# Convenience functions
async def retry_async(operation: Callable, *args, **kwargs) -> Any:
    """Retry an async operation with default configuration"""
    return await default_retry_handler.execute_with_retry(operation, *args, **kwargs)


def retry_sync(operation: Callable, *args, **kwargs) -> Any:
    """Retry a sync operation with default configuration"""
    return default_retry_handler.execute_sync_with_retry(operation, *args, **kwargs)
