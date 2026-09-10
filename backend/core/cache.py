import time
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


class CacheProvider(ABC):
    """Abstract interface for caching providers."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Set."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete."""
        pass


class InMemoryCache(CacheProvider):
    """
    In-memory TTL cache implementation using Python dictionary.
    Thread-safe in asyncio environments (single threaded event loop).
    """
    def __init__(self) -> None:
        """  init  ."""
        self._store: Dict[str, Dict[str, Any]] = {}

    async def get(self, key: str) -> Optional[Any]:
        """Get."""
        entry = self._store.get(key)
        if not entry:
            return None
            
        if time.time() > entry["expires_at"]:
            # Expired
            del self._store[key]
            return None
            
        return entry["value"]

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set."""
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + ttl_seconds
        }

    async def delete(self, key: str) -> None:
        """Delete."""
        if key in self._store:
            del self._store[key]


# Singleton instance for simple app-wide in-memory caching
memory_cache = InMemoryCache()
