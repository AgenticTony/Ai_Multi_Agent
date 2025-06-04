"""Caching utilities for performance optimization"""

import asyncio
import logging
import time
from typing import Any, Optional, Dict, Callable, Union, TypeVar, Generic
from functools import wraps
import hashlib
import json
from datetime import datetime, timedelta
from app.config.settings import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheEntry(Generic[T]):
    """Cache entry with expiration and metadata"""
    
    def __init__(self, value: T, ttl: int = None):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl or settings.cache_ttl
        self.access_count = 0
        self.last_accessed = self.created_at
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() - self.created_at > self.ttl
    
    def access(self) -> T:
        """Access the cached value and update metadata"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value
    
    @property
    def age(self) -> float:
        """Get age of cache entry in seconds"""
        return time.time() - self.created_at


class InMemoryCache:
    """Thread-safe in-memory cache with TTL and LRU eviction"""
    
    def __init__(self, max_size: int = None, default_ttl: int = None):
        self.max_size = max_size or settings.cache_max_size
        self.default_ttl = default_ttl or settings.cache_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expired": 0
        }
    
    def _generate_key(self, key: Union[str, tuple, dict]) -> str:
        """Generate a cache key from various input types"""
        if isinstance(key, str):
            return key
        elif isinstance(key, (tuple, list)):
            return hashlib.md5(str(key).encode()).hexdigest()
        elif isinstance(key, dict):
            # Sort dict for consistent hashing
            sorted_items = sorted(key.items())
            return hashlib.md5(str(sorted_items).encode()).hexdigest()
        else:
            return hashlib.md5(str(key).encode()).hexdigest()
    
    async def get(self, key: Union[str, tuple, dict]) -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._generate_key(key)
        
        async with self._lock:
            entry = self._cache.get(cache_key)
            
            if entry is None:
                self._stats["misses"] += 1
                return None
            
            if entry.is_expired:
                del self._cache[cache_key]
                self._stats["expired"] += 1
                self._stats["misses"] += 1
                return None
            
            self._stats["hits"] += 1
            return entry.access()
    
    async def set(self, key: Union[str, tuple, dict], value: Any, ttl: int = None) -> None:
        """Set value in cache"""
        cache_key = self._generate_key(key)
        entry_ttl = ttl or self.default_ttl
        
        async with self._lock:
            # Check if we need to evict entries
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                await self._evict_lru()
            
            self._cache[cache_key] = CacheEntry(value, entry_ttl)
    
    async def delete(self, key: Union[str, tuple, dict]) -> bool:
        """Delete value from cache"""
        cache_key = self._generate_key(key)
        
        async with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self._cache.clear()
            self._stats = {
                "hits": 0,
                "misses": 0,
                "evictions": 0,
                "expired": 0
            }
    
    async def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self._cache:
            return
        
        # Find LRU entry
        lru_key = min(self._cache.keys(), 
                     key=lambda k: self._cache[k].last_accessed)
        
        del self._cache[lru_key]
        self._stats["evictions"] += 1
        
        logger.debug(f"Evicted LRU cache entry: {lru_key}")
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries and return count"""
        expired_count = 0
        
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
                expired_count += 1
            
            self._stats["expired"] += expired_count
        
        if expired_count > 0:
            logger.debug(f"Cleaned up {expired_count} expired cache entries")
        
        return expired_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self._stats,
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests
        }
    
    def get_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""
        entries_info = []
        
        for key, entry in self._cache.items():
            entries_info.append({
                "key": key[:50] + "..." if len(key) > 50 else key,
                "age": round(entry.age, 2),
                "ttl": entry.ttl,
                "access_count": entry.access_count,
                "is_expired": entry.is_expired
            })
        
        return {
            "stats": self.get_stats(),
            "entries": entries_info
        }


class CacheManager:
    """Global cache manager with multiple cache instances"""
    
    def __init__(self):
        self.caches: Dict[str, InMemoryCache] = {}
        self._default_cache = InMemoryCache()
    
    def get_cache(self, name: str = "default") -> InMemoryCache:
        """Get or create a named cache instance"""
        if name == "default":
            return self._default_cache
        
        if name not in self.caches:
            self.caches[name] = InMemoryCache()
        
        return self.caches[name]
    
    async def cleanup_all_expired(self) -> Dict[str, int]:
        """Cleanup expired entries from all caches"""
        results = {}
        
        # Cleanup default cache
        results["default"] = await self._default_cache.cleanup_expired()
        
        # Cleanup named caches
        for name, cache in self.caches.items():
            results[name] = await cache.cleanup_expired()
        
        return results
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics from all caches"""
        stats = {}
        
        stats["default"] = self._default_cache.get_stats()
        
        for name, cache in self.caches.items():
            stats[name] = cache.get_stats()
        
        return stats


# Global cache manager instance
cache_manager = CacheManager()


# Decorator for caching function results
def cached(
    ttl: int = None,
    cache_name: str = "default",
    key_func: Optional[Callable] = None,
    skip_cache_if: Optional[Callable] = None
):
    """Decorator to cache function results"""
    
    def decorator(func: Callable) -> Callable:
        cache = cache_manager.get_cache(cache_name)
        
        def generate_cache_key(*args, **kwargs) -> str:
            """Generate cache key for function call"""
            if key_func:
                return key_func(*args, **kwargs)
            
            # Default key generation
            key_parts = [func.__name__]
            if args:
                key_parts.extend(str(arg) for arg in args)
            if kwargs:
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            
            return "|".join(key_parts)
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Check if we should skip cache
                if skip_cache_if and skip_cache_if(*args, **kwargs):
                    return await func(*args, **kwargs)
                
                cache_key = generate_cache_key(*args, **kwargs)
                
                # Try to get from cache
                cached_result = await cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                    return cached_result
                
                # Execute function and cache result
                logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
                result = await func(*args, **kwargs)
                await cache.set(cache_key, result, ttl)
                
                return result
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Check if we should skip cache
                if skip_cache_if and skip_cache_if(*args, **kwargs):
                    return func(*args, **kwargs)
                
                cache_key = generate_cache_key(*args, **kwargs)
                
                # Try to get from cache (need to run in event loop)
                try:
                    loop = asyncio.get_event_loop()
                    cached_result = loop.run_until_complete(cache.get(cache_key))
                    
                    if cached_result is not None:
                        logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                        return cached_result
                    
                    # Execute function and cache result
                    logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
                    result = func(*args, **kwargs)
                    loop.run_until_complete(cache.set(cache_key, result, ttl))
                    
                    return result
                    
                except RuntimeError:
                    # No event loop, execute without caching
                    logger.warning(f"No event loop available for caching {func.__name__}")
                    return func(*args, **kwargs)
            
            return sync_wrapper
    
    return decorator


# Convenience functions
async def get_cached(key: Union[str, tuple, dict], cache_name: str = "default") -> Optional[Any]:
    """Get value from cache"""
    cache = cache_manager.get_cache(cache_name)
    return await cache.get(key)


async def set_cached(key: Union[str, tuple, dict], value: Any, 
                    ttl: int = None, cache_name: str = "default") -> None:
    """Set value in cache"""
    cache = cache_manager.get_cache(cache_name)
    await cache.set(key, value, ttl)


async def delete_cached(key: Union[str, tuple, dict], cache_name: str = "default") -> bool:
    """Delete value from cache"""
    cache = cache_manager.get_cache(cache_name)
    return await cache.delete(key)


async def clear_cache(cache_name: str = "default") -> None:
    """Clear cache"""
    cache = cache_manager.get_cache(cache_name)
    await cache.clear()


# Background task for cache cleanup
async def cache_cleanup_task():
    """Background task to periodically clean up expired cache entries"""
    while True:
        try:
            await asyncio.sleep(300)  # Run every 5 minutes
            results = await cache_manager.cleanup_all_expired()
            
            total_cleaned = sum(results.values())
            if total_cleaned > 0:
                logger.info(f"Cache cleanup: removed {total_cleaned} expired entries")
                
        except Exception as e:
            logger.error(f"Error in cache cleanup task: {str(e)}")


# Cache-specific decorators for common use cases
def cache_memory_results(ttl: int = 300):
    """Cache memory system results"""
    return cached(ttl=ttl, cache_name="memory")


def cache_openai_results(ttl: int = 600):
    """Cache OpenAI API results"""
    return cached(ttl=ttl, cache_name="openai")


def cache_user_data(ttl: int = 900):
    """Cache user data"""
    return cached(ttl=ttl, cache_name="users")
