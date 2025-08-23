# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Intelligent caching system for prompt fitting operations.

This module provides sophisticated caching capabilities that can dramatically
improve performance for repeated or similar content fitting operations while
maintaining data integrity guarantees.
"""

from abc import ABC
from abc import abstractmethod
import asyncio
from collections import OrderedDict
from dataclasses import dataclass
from dataclasses import field
import hashlib
import json
from pathlib import Path
import pickle  # nosec B403
import time
from typing import Any, Generic, Optional

import aiofiles

from .logging import get_logger
from .prompt_fitting import ContentFitter
from .prompt_fitting import ContentFitterT
from .prompt_fitting import FittingResult
from .prompt_fitting import FittingStrategy
from .prompt_fitting import PromptFittingConfig
from .prompt_fitting import TokenCounter

# Constants for magic values
CONTENT_SAMPLE_SIZE = 1024
CONTENT_HASH_THRESHOLD = 2048
HASH_LENGTH = 16


@dataclass
class CacheStatistics:
    """Cache performance statistics."""

    cache_hits: int = 0
    cache_misses: int = 0
    similarity_matches: int = 0

    @property
    def total_requests(self) -> int:
        """Get total cache requests."""
        return self.cache_hits + self.cache_misses

    @property
    def hit_rate(self) -> float:
        """Get cache hit rate as percentage."""
        return (self.cache_hits / self.total_requests * 100) if self.total_requests > 0 else 0.0

    def reset(self) -> None:
        """Reset all statistics."""
        self.cache_hits = 0
        self.cache_misses = 0
        self.similarity_matches = 0


@dataclass
class CachedContentFitterConfig:
    """Parameter class for CachedContentFitter initialization."""

    base_fitter: ContentFitter
    config: PromptFittingConfig
    token_counter: TokenCounter
    cache_backend: Optional["CacheBackend"] = None
    cache_ttl_hours: float = 24.0
    enable_similarity_matching: bool = True


@dataclass
class CacheKey:
    """Composite key for caching fitting operations."""

    content_hash: str
    target_tokens: int
    strategy: str
    config_hash: str

    def to_string(self) -> str:
        """Convert cache key to string representation."""
        return f"{self.content_hash}:{self.target_tokens}:{self.strategy}:{self.config_hash}"

    @classmethod
    def from_content(
        cls,
        content: str,
        target_tokens: int,
        strategy: FittingStrategy,
        config: PromptFittingConfig,
    ) -> "CacheKey":
        """Create cache key from fitting parameters."""

        # Create content hash (using first 1KB and last 1KB + length for efficiency)
        content_sample = (
            content[:CONTENT_SAMPLE_SIZE] + content[-CONTENT_SAMPLE_SIZE:]
            if len(content) > CONTENT_HASH_THRESHOLD
            else content
        )
        content_hash = hashlib.sha256(f"{len(content)}:{content_sample}".encode()).hexdigest()[
            :HASH_LENGTH
        ]

        # Create config hash from relevant fields
        config_dict = {
            "max_tokens": config.max_tokens,
            "overlap_ratio": config.overlap_ratio,
            "min_chunk_size": config.min_chunk_size,
            "preserve_structure": config.preserve_structure,
            "validation_enabled": config.validation_enabled,
            "strict_mode": config.strict_mode,
        }
        config_hash = hashlib.sha256(json.dumps(config_dict, sort_keys=True).encode()).hexdigest()[
            :8
        ]

        return cls(
            content_hash=content_hash,
            target_tokens=target_tokens,
            strategy=strategy.value,
            config_hash=config_hash,
        )


@dataclass
class CacheEntry(Generic[ContentFitterT]):
    """Entry stored in the fitting cache."""

    key: CacheKey
    result: FittingResult[ContentFitterT]
    created_at: float
    access_count: int = 0
    last_accessed: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize computed fields."""
        if self.last_accessed == 0.0:
            self.last_accessed = self.created_at

    @property
    def age_seconds(self) -> float:
        """Get entry age in seconds."""
        return time.time() - self.created_at

    @property
    def time_since_access(self) -> float:
        """Get time since last access in seconds."""
        return time.time() - self.last_accessed

    def access(self) -> "CacheEntry[ContentFitterT]":
        """Mark entry as accessed and return self."""
        self.access_count += 1
        self.last_accessed = time.time()
        return self


class CacheBackend(ABC):
    """Abstract base for cache storage backends."""

    @abstractmethod
    async def get(self, key: str) -> CacheEntry[Any] | None:
        """Get cache entry by key."""
        raise NotImplementedError

    @abstractmethod
    async def set(self, key: str, entry: CacheEntry[Any]) -> None:
        """Set cache entry."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete cache entry, return True if existed."""
        raise NotImplementedError

    @abstractmethod
    async def clear(self) -> int:
        """Clear all entries, return count of deleted entries."""
        raise NotImplementedError

    @abstractmethod
    async def size(self) -> int:
        """Get number of entries in cache."""
        raise NotImplementedError

    @abstractmethod
    async def keys(self) -> list[str]:
        """Get all cache keys."""
        raise NotImplementedError


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend with LRU eviction."""

    def __init__(self, max_entries: int = 1000):
        """Initialize memory cache with maximum entry limit."""
        self.max_entries = max_entries
        self.cache: OrderedDict[str, CacheEntry[Any]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> CacheEntry[Any] | None:
        """Get entry and move to end (LRU)."""
        async with self._lock:
            if key in self.cache:
                entry = self.cache.pop(key)  # Remove and re-add to make it most recent
                self.cache[key] = entry
                return entry.access()
            return None

    async def set(self, key: str, entry: CacheEntry[Any]) -> None:
        """Set entry, evicting oldest if necessary."""
        async with self._lock:
            if key in self.cache:
                self.cache.pop(key)  # Remove existing

            self.cache[key] = entry

            # Evict oldest entries if over limit
            for _ in range(len(self.cache) - self.max_entries):
                if len(self.cache) <= self.max_entries:
                    break
                self.cache.popitem(last=False)

    async def delete(self, key: str) -> bool:
        """Delete entry."""
        async with self._lock:
            return self.cache.pop(key, None) is not None

    async def clear(self) -> int:
        """Clear all entries."""
        async with self._lock:
            count = len(self.cache)
            self.cache.clear()
            return count

    async def size(self) -> int:
        """Get cache size."""
        return len(self.cache)

    async def keys(self) -> list[str]:
        """Get all keys."""
        return list(self.cache.keys())


class FileCacheBackend(CacheBackend):
    """File-based cache backend for persistent storage."""

    def __init__(self, cache_dir: Path, max_file_age_hours: float = 24.0):
        """Initialize file cache.

        Args:
            cache_dir: Directory to store cache files
            max_file_age_hours: Maximum age of cache files in hours
        """
        self.cache_dir = Path(cache_dir)
        self.max_file_age = max_file_age_hours * 3600  # Convert to seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    def _get_file_path(self, key: str) -> Path:
        """Get file path for cache key."""
        safe_key = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{safe_key}.cache"

    async def get(self, key: str) -> CacheEntry[Any] | None:
        """Get entry from file."""
        file_path = self._get_file_path(key)

        if not file_path.exists():
            return None

        try:
            # Check file age
            if time.time() - file_path.stat().st_mtime > self.max_file_age:
                await asyncio.to_thread(file_path.unlink)
                return None

            async with aiofiles.open(file_path, "rb") as f:
                data = await f.read()
                entry: CacheEntry[Any] = pickle.loads(data)  # nosec B301
                return entry.access()

        except (OSError, pickle.UnpicklingError, EOFError, ValueError):
            # Corrupted or invalid file, remove it
            try:
                await asyncio.to_thread(file_path.unlink)
            except OSError as e:
                # File deletion failed, log but continue
                get_logger().debug(f"Failed to remove corrupted cache file {file_path}: {e}")
            return None

    async def set(self, key: str, entry: CacheEntry[Any]) -> None:
        """Set entry to file."""
        file_path = self._get_file_path(key)

        try:
            async with self._lock:
                data = pickle.dumps(entry)
                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(data)
        except (OSError, pickle.PicklingError) as e:
            # Log error but don't fail the operation
            logger = get_logger()
            logger.warning(f"Failed to write cache entry to {file_path}: {e}")

    async def delete(self, key: str) -> bool:
        """Delete cache file."""
        file_path = self._get_file_path(key)
        try:
            if file_path.exists():
                await asyncio.to_thread(file_path.unlink)
                return True
        except OSError as e:
            # File deletion failed, log but continue
            get_logger().debug(f"Failed to delete cache file {file_path}: {e}")
        return False

    async def clear(self) -> int:
        """Clear all cache files."""
        count = 0
        try:
            for file_path in self.cache_dir.glob("*.cache"):
                try:
                    await asyncio.to_thread(file_path.unlink)
                    count += 1
                except OSError as e:
                    # Individual file deletion failed, log but continue
                    get_logger().debug(f"Failed to delete cache file {file_path}: {e}")
        except OSError as e:
            # Cache directory access failed, log but continue
            get_logger().debug(f"Failed to access cache directory {self.cache_dir}: {e}")
        return count

    async def size(self) -> int:
        """Get number of cache files."""
        try:
            return len(list(self.cache_dir.glob("*.cache")))
        except OSError:
            return 0

    async def keys(self) -> list[str]:
        """Get all cache keys (expensive operation)."""
        keys = []
        try:
            for file_path in self.cache_dir.glob("*.cache"):
                try:
                    async with aiofiles.open(file_path, "rb") as f:
                        data = await f.read()
                        entry = pickle.loads(data)  # nosec B301
                        keys.append(entry.key.to_string())
                except (OSError, pickle.UnpicklingError, EOFError):
                    continue
        except OSError as e:
            # Cache directory access failed, log but continue
            get_logger().debug(f"Failed to list cache directory {self.cache_dir}: {e}")
        return keys


class CachedContentFitter(ContentFitter):
    """Content fitter wrapper that adds intelligent caching capabilities."""

    def __init__(self, config: CachedContentFitterConfig):
        """Initialize cached content fitter.

        Args:
            config: CachedContentFitterConfig containing all initialization parameters
        """
        super().__init__(config.config, config.token_counter)
        self.base_fitter = config.base_fitter
        self.cache_backend = config.cache_backend or MemoryCacheBackend()
        self.cache_ttl = config.cache_ttl_hours * 3600  # Convert to seconds
        self.enable_similarity = config.enable_similarity_matching
        self.logger = get_logger(f"Cached_{config.base_fitter.__class__.__name__}")
        self.statistics = CacheStatistics()

    async def fit_content(self, content: str, target_tokens: int) -> FittingResult[ContentFitterT]:
        """Fit content with intelligent caching."""

        # Create cache key
        strategy = getattr(self.base_fitter, "strategy", FittingStrategy.OVERLAPPING_CHUNKS)
        cache_key = CacheKey.from_content(content, target_tokens, strategy, self.config)
        key_string = cache_key.to_string()

        # Try exact cache hit first
        cached_entry = await self.cache_backend.get(key_string)
        if cached_entry and self._is_cache_valid(cached_entry):
            self.statistics.cache_hits += 1
            self.logger.debug(f"Cache hit for key: {key_string[:32]}...")

            # Return cached result with updated metadata
            result = cached_entry.result
            result.metadata.update(
                {
                    "cache_hit": True,
                    "cache_age_seconds": cached_entry.age_seconds,
                    "cache_access_count": cached_entry.access_count,
                }
            )
            return result

        # Try similarity matching if enabled
        if self.enable_similarity and (
            similar_entry := await self._find_similar_cached_result(
                content, target_tokens, strategy
            )
        ):
            self.statistics.similarity_matches += 1
            self.logger.debug(f"Similarity match found for content (length: {len(content)})")

            result = similar_entry.result
            result.metadata.update(
                {
                    "cache_hit": True,
                    "similarity_match": True,
                    "cache_age_seconds": similar_entry.age_seconds,
                }
            )
            return result

        # Cache miss - compute result
        self.statistics.cache_misses += 1
        self.logger.debug(f"Cache miss for key: {key_string[:32]}...")

        start_time = time.time()
        result = await self.base_fitter.fit_content(content, target_tokens)
        processing_time = time.time() - start_time

        # Cache the result
        cache_entry = CacheEntry(
            key=cache_key,
            result=result,
            created_at=time.time(),
            metadata={"processing_time": processing_time, "content_length": len(content)},
        )

        await self.cache_backend.set(key_string, cache_entry)

        # Update result metadata
        result.metadata.update(
            {"cache_hit": False, "processing_time": processing_time, "cached": True}
        )

        return result

    def _is_cache_valid(self, entry: CacheEntry[Any]) -> bool:
        """Check if cache entry is still valid."""
        return entry.age_seconds <= self.cache_ttl

    async def _find_similar_cached_result(
        self, content: str, target_tokens: int, strategy: FittingStrategy
    ) -> CacheEntry[Any] | None:
        """Find similar cached result using fuzzy matching."""

        # For performance, limit similarity search to recent entries
        all_keys = await self.cache_backend.keys()

        # Look for entries with similar parameters
        content_length = len(content)
        target_length_range = (content_length * 0.8, content_length * 1.2)
        target_tokens_range = (target_tokens * 0.9, target_tokens * 1.1)

        for key_string in all_keys[:100]:  # Limit search scope
            try:
                entry = await self.cache_backend.get(key_string)
                if not entry or not self._is_cache_valid(entry):
                    continue

                # Check if parameters are similar
                if (
                    entry.key.strategy == strategy.value
                    and target_tokens_range[0] <= entry.key.target_tokens <= target_tokens_range[1]
                ):

                    # Check content similarity through metadata
                    cached_length = entry.metadata.get("content_length", 0)
                    if target_length_range[0] <= cached_length <= target_length_range[1]:
                        return entry

            except (OSError, pickle.UnpicklingError, EOFError, ValueError):
                continue

        return None

    async def clear_cache(self) -> int:
        """Clear all cached entries."""
        count = await self.cache_backend.clear()
        self.statistics.reset()
        return count

    async def get_cache_stats(self) -> dict[str, Any]:
        """Get comprehensive cache statistics."""
        cache_size = await self.cache_backend.size()

        stats = {
            "cache_size": cache_size,
            "cache_hits": self.statistics.cache_hits,
            "cache_misses": self.statistics.cache_misses,
            "similarity_matches": self.statistics.similarity_matches,
            "total_requests": self.statistics.total_requests,
            "hit_rate": self.statistics.hit_rate,
            "backend_type": type(self.cache_backend).__name__,
        }

        return stats

    async def prune_expired_entries(self) -> int:
        """Remove expired cache entries."""
        pruned_count = 0

        try:
            all_keys = await self.cache_backend.keys()

            for key_string in all_keys:
                entry = await self.cache_backend.get(key_string)
                if entry and not self._is_cache_valid(entry):
                    await self.cache_backend.delete(key_string)
                    pruned_count += 1

        except (OSError, pickle.UnpicklingError, EOFError, ValueError) as e:
            self.logger.warning(f"Error during cache pruning: {e}")

        if pruned_count > 0:
            self.logger.info(f"Pruned {pruned_count} expired cache entries")

        return pruned_count

    def validate_preservation(self, original: str, fitted: str) -> bool:
        """Delegate validation to base fitter."""
        return self.base_fitter.validate_preservation(original, fitted)

    async def warm_cache(self, content_samples: list[tuple[str, int]]) -> int:
        """Warm the cache with common content patterns.

        Args:
            content_samples: List of (content, target_tokens) tuples

        Returns:
            Number of entries added to cache
        """
        warmed_count = 0

        self.logger.info(f"Warming cache with {len(content_samples)} samples")

        for content, target_tokens in content_samples:
            try:
                # Only warm cache if not already present
                strategy = getattr(self.base_fitter, "strategy", FittingStrategy.OVERLAPPING_CHUNKS)
                cache_key = CacheKey.from_content(content, target_tokens, strategy, self.config)

                if await self.cache_backend.get(cache_key.to_string()) is None:
                    await self.fit_content(content, target_tokens)
                    warmed_count += 1

            except (OSError, pickle.UnpicklingError, EOFError, ValueError) as e:
                self.logger.warning(f"Failed to warm cache for content sample: {e}")

        self.logger.info(f"Cache warming complete: {warmed_count} new entries added")
        return warmed_count
