# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Blackcat Informatics® Inc.

"""Plugin architecture for extensible prompt fitting strategies.

This module provides a comprehensive plugin system that allows for
dynamic registration and discovery of custom fitting strategies while
maintaining strict data integrity requirements.
"""

from abc import ABC
from abc import abstractmethod
import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
import importlib
import importlib.util
import inspect
from pathlib import Path
import sys
from typing import Any, Optional, Protocol
import warnings

from .logging import get_logger
from .prompt_fitting import ContentFitter
from .prompt_fitting import PromptFittingConfig
from .prompt_fitting import TokenCount
from .prompt_fitting import TokenCounter


class PluginPriority(Enum):
    """Priority levels for plugin execution order."""

    CRITICAL = 100  # System-critical plugins (highest priority)
    HIGH = 75  # High-priority custom strategies
    NORMAL = 50  # Standard plugins (default)
    LOW = 25  # Fallback or experimental strategies
    EXPERIMENTAL = 10  # Lowest priority for testing


class PluginStatus(Enum):
    """Status of a plugin in the system."""

    REGISTERED = "registered"
    LOADED = "loaded"
    ACTIVE = "active"
    DISABLED = "disabled"
    FAILED = "failed"
    DEPRECATED = "deprecated"


@dataclass
class PluginInfo:
    """Basic plugin information."""

    name: str
    version: str
    description: str
    author: str
    tags: list[str] = field(default_factory=list)


@dataclass
class PluginDependencies:
    """Plugin dependency and conflict information."""

    dependencies: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    min_python_version: str = "3.12"


@dataclass
class PluginCapabilities:
    """Plugin capabilities and constraints."""

    supported_content_types: set[str] = field(default_factory=set)
    max_token_limit: Optional[int] = None
    requires_validation: bool = True
    data_integrity_certified: bool = False  # Must be True for production use


@dataclass
class PluginFlags:
    """Plugin status flags."""

    experimental: bool = False
    deprecated: bool = False


@dataclass
class PluginMetadata:
    """Comprehensive metadata for a prompt fitting plugin."""

    # Basic information
    info: PluginInfo
    priority: PluginPriority = PluginPriority.NORMAL

    # Grouped metadata
    dependency_info: PluginDependencies = field(default_factory=PluginDependencies)
    capabilities: PluginCapabilities = field(default_factory=PluginCapabilities)
    flags: PluginFlags = field(default_factory=PluginFlags)

    @property
    def name(self) -> str:
        """Get plugin name from info."""
        return self.info.name

    @property
    def version(self) -> str:
        """Get plugin version from info."""
        return self.info.version

    @property
    def data_integrity_certified(self) -> bool:
        """Get data integrity certification from capabilities."""
        return self.capabilities.data_integrity_certified

    @property
    def experimental(self) -> bool:
        """Get experimental flag from flags."""
        return self.flags.experimental

    @property
    def supported_content_types(self) -> set[str]:
        """Get supported content types from capabilities."""
        return self.capabilities.supported_content_types


class PluginInterface(Protocol):
    """Protocol that all prompt fitting plugins must implement."""

    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        raise NotImplementedError

    def create_fitter(
        self, config: PromptFittingConfig, token_counter: TokenCounter
    ) -> ContentFitter:
        """Create a content fitter instance."""
        raise NotImplementedError

    def is_compatible(self, content: str, target_tokens: int) -> bool:
        """Check if this plugin can handle the given content."""
        raise NotImplementedError

    async def validate_plugin(self) -> bool:
        """Validate plugin functionality and data integrity compliance."""
        raise NotImplementedError


@dataclass
class PluginCore:
    """Core plugin registration data."""

    plugin_class: type[PluginInterface]
    metadata: PluginMetadata
    status: PluginStatus
    instance: Optional[PluginInterface] = None


@dataclass
class PluginStats:
    """Plugin usage and error statistics."""

    load_time: float
    last_used: Optional[float] = None
    usage_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None


@dataclass
class PluginRegistration:
    """Registration record for a plugin."""

    core: PluginCore
    stats: PluginStats


class BasePlugin(ABC):
    """Abstract base class for prompt fitting plugins."""

    def __init__(self) -> None:
        """Initialize the base plugin."""
        self.logger = get_logger(f"Plugin_{self.__class__.__name__}")

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata - must be implemented by subclasses."""
        raise NotImplementedError

    @abstractmethod
    def create_fitter(
        self, config: PromptFittingConfig, token_counter: TokenCounter
    ) -> ContentFitter:
        """Create a content fitter instance - must be implemented by subclasses."""
        raise NotImplementedError

    def is_compatible(self, _content: str, target_tokens: int) -> bool:
        """Default compatibility check - can be overridden."""
        # Default: compatible if not exceeding max token limit
        if self.metadata.capabilities.max_token_limit is not None:
            return target_tokens <= self.metadata.capabilities.max_token_limit
        return True

    async def validate_plugin(self) -> bool:
        """Default validation - can be overridden for custom checks."""
        try:
            # Test plugin instantiation
            mock_config = PromptFittingConfig(max_tokens=TokenCount(1000))

            class MockTokenCounter:
                """Mock token counter for plugin validation."""

                async def count_tokens(self, content: str) -> TokenCount:
                    """Count tokens using simple character-based estimation."""
                    return TokenCount(len(content) // 4)

                def get_token_count(self, content: str) -> int:
                    """Synchronous version of token counting for compatibility."""
                    return len(content) // 4

            fitter = self.create_fitter(mock_config, MockTokenCounter())

            # Run validation checks
            validation_errors = []

            # Test basic functionality
            test_content = "This is a test content for plugin validation."
            result = await fitter.fit_content(test_content, 100)

            # Project compliance check: data must be preserved
            if not result.data_preserved:
                validation_errors.append("violates data integrity requirement")

            if validation_errors:
                for error in validation_errors:
                    self.logger.error(f"Plugin {self.metadata.info.name} {error}")
                return False

            self.logger.info(f"Plugin {self.metadata.info.name} passed validation")
            return True

        except (TypeError, ValueError, AttributeError, ImportError) as e:
            self.logger.error(f"Plugin validation failed for {self.metadata.info.name}: {e}")
            return False


class PluginRegistry:
    """Central registry for managing prompt fitting plugins."""

    def __init__(self) -> None:
        """Initialize the plugin registry."""
        self.plugins: dict[str, PluginRegistration] = {}
        self.logger = get_logger("PluginRegistry")
        self._discovery_paths: list[Path] = []
        self._auto_discovery_enabled = True
        self._strict_mode = True  # Enforce project data integrity requirements

    def register_plugin(
        self, plugin_class: type[PluginInterface], force_override: bool = False
    ) -> bool:
        """Register a plugin class in the registry.

        Args:
            plugin_class: The plugin class to register
            force_override: Allow overriding existing plugins

        Returns:
            bool: True if registration successful
        """
        try:
            # Create temporary instance to get metadata
            plugin_instance = plugin_class()
            metadata = plugin_instance.metadata

            # Check if plugin already exists
            if metadata.info.name in self.plugins and not force_override:
                self.logger.warning(
                    f"Plugin {metadata.info.name} already registered. "
                    f"Use force_override=True to replace."
                )
                return False

            # Validate plugin requirements
            if not self._validate_plugin_requirements(metadata):
                return False

            # Create registration
            plugin_core = PluginCore(
                plugin_class=plugin_class,
                metadata=metadata,
                status=PluginStatus.REGISTERED,
                instance=plugin_instance,
            )
            plugin_stats = PluginStats(
                load_time=asyncio.get_event_loop().time(),
            )
            registration = PluginRegistration(
                core=plugin_core,
                stats=plugin_stats,
            )

            self.plugins[metadata.info.name] = registration
            self.logger.info(
                f"Successfully registered plugin: {metadata.info.name} v{metadata.info.version}"
            )
            return True

        except (TypeError, ValueError, AttributeError, ImportError) as e:
            self.logger.error(f"Failed to register plugin {plugin_class.__name__}: {e}")
            return False

    def _validate_plugin_requirements(self, metadata: PluginMetadata) -> bool:
        """Validate plugin meets system requirements."""
        # Check Python version
        current_python = f"{sys.version_info.major}.{sys.version_info.minor}"
        if metadata.dependency_info.min_python_version > current_python:
            self.logger.error(
                f"Plugin {metadata.info.name} requires Python "
                f"{metadata.dependency_info.min_python_version}, but running {current_python}"
            )
            return False

        # Project compliance check
        if self._strict_mode and not metadata.capabilities.data_integrity_certified:
            self.logger.error(
                f"Plugin {metadata.info.name} is not certified for data integrity. "
                f"This violates project requirements in strict mode."
            )
            return False

        # Check for conflicts
        for conflict in metadata.dependency_info.conflicts:
            if conflict in self.plugins:
                self.logger.error(
                    f"Plugin {metadata.info.name} conflicts with already loaded plugin: {conflict}"
                )
                return False

        # Validate dependencies
        for dep in metadata.dependency_info.dependencies:
            if dep not in self.plugins:
                self.logger.warning(
                    f"Plugin {metadata.info.name} depends on {dep} which is not loaded"
                )

        return True

    async def load_plugin(self, plugin_name: str) -> bool:
        """Load and activate a registered plugin."""
        if plugin_name not in self.plugins:
            self.logger.error(f"Plugin {plugin_name} not found in registry")
            return False

        registration = self.plugins[plugin_name]

        try:
            # Validate plugin before loading
            if (
                registration.core.instance
                and not await registration.core.instance.validate_plugin()
            ):
                # Plugin validation failed
                status = PluginStatus.FAILED
                registration.stats.last_error = "Plugin validation failed"
            else:
                # Plugin is valid - load it
                status = PluginStatus.LOADED
                self.logger.info(f"Successfully loaded plugin: {plugin_name}")

            registration.core.status = status
            return status == PluginStatus.LOADED

        except (TypeError, ValueError, AttributeError, ImportError, RuntimeError) as e:
            registration.core.status = PluginStatus.FAILED
            registration.stats.last_error = str(e)
            registration.stats.error_count += 1
            self.logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return False

    def get_compatible_plugins(
        self, content: str, target_tokens: int, content_type: Optional[str] = None
    ) -> list[PluginRegistration]:
        """Get plugins compatible with the given content and constraints.

        Args:
            content: Content to be processed
            target_tokens: Target token limit
            content_type: Optional content type filter

        Returns:
            List of compatible plugin registrations sorted by priority
        """
        compatible_plugins = []

        for registration in self.plugins.values():
            # Skip if not loaded or failed
            if registration.core.status not in [PluginStatus.LOADED, PluginStatus.ACTIVE]:
                continue

            # Check content type compatibility
            if (
                content_type
                and registration.core.metadata.capabilities.supported_content_types
                and content_type
                not in registration.core.metadata.capabilities.supported_content_types
            ):
                continue

            # Check plugin-specific compatibility
            if registration.core.instance and registration.core.instance.is_compatible(
                content, target_tokens
            ):
                compatible_plugins.append(registration)

        # Sort by priority (highest first)
        compatible_plugins.sort(key=lambda r: r.core.metadata.priority.value, reverse=True)

        return compatible_plugins

    def unregister_plugin(self, plugin_name: str) -> bool:
        """Unregister a plugin from the registry."""
        if plugin_name not in self.plugins:
            return False

        _ = self.plugins.pop(plugin_name)  # Remove plugin from registry
        self.logger.info(f"Unregistered plugin: {plugin_name}")
        return True

    def list_plugins(
        self, status_filter: Optional[PluginStatus] = None
    ) -> list[PluginRegistration]:
        """List all registered plugins, optionally filtered by status."""
        plugins = list(self.plugins.values())

        if status_filter:
            plugins = [p for p in plugins if p.core.status == status_filter]

        # Sort by priority and name
        plugins.sort(
            key=lambda p: (p.core.metadata.priority.value, p.core.metadata.info.name), reverse=True
        )
        return plugins

    def get_plugin_stats(self) -> dict[str, Any]:
        """Get comprehensive statistics about registered plugins."""
        total_plugins = len(self.plugins)
        status_counts: dict[str, int] = {}
        priority_counts: dict[str, int] = {}

        for registration in self.plugins.values():
            # Count by status
            status = registration.core.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            # Count by priority
            priority_str = str(registration.core.metadata.priority.value)
            priority_counts[priority_str] = priority_counts.get(priority_str, 0) + 1

        return {
            "total_plugins": total_plugins,
            "status_distribution": status_counts,
            "priority_distribution": priority_counts,
            "average_usage": (
                sum(r.stats.usage_count for r in self.plugins.values()) / max(1, total_plugins)
            ),
            "error_rate": (
                sum(r.stats.error_count for r in self.plugins.values()) / max(1, total_plugins)
            ),
        }

    def add_discovery_path(self, path: Path) -> None:
        """Add a directory path for automatic plugin discovery."""
        if path.exists() and path.is_dir():
            self._discovery_paths.append(path)
            self.logger.info(f"Added plugin discovery path: {path}")
        else:
            self.logger.warning(f"Invalid discovery path: {path}")

    def discover_plugins(self) -> int:
        """Automatically discover and register plugins from discovery paths.

        Returns:
            int: Number of plugins discovered and registered
        """
        if not self._auto_discovery_enabled:
            return 0

        discovered_count = 0

        for discovery_path in self._discovery_paths:
            try:
                for plugin_file in discovery_path.glob("**/*_plugin.py"):
                    if self._load_plugin_from_file(plugin_file):
                        discovered_count += 1
            except (OSError, ImportError, AttributeError) as e:
                self.logger.error(f"Error during plugin discovery in {discovery_path}: {e}")

        self.logger.info(f"Plugin discovery complete: {discovered_count} plugins found")
        return discovered_count

    def _load_plugin_from_file(self, plugin_file: Path) -> bool:
        """Load a plugin from a Python file."""
        try:
            # Import the plugin module
            if (
                spec := importlib.util.spec_from_file_location("plugin_module", plugin_file)
            ) is None:
                self.logger.error(f"Failed to create module spec for {plugin_file}")
                return False
            module = importlib.util.module_from_spec(spec)
            if spec.loader is None:
                self.logger.error(f"No loader available for {plugin_file}")
                return False
            spec.loader.exec_module(module)

            # Look for plugin classes
            for _name, obj in inspect.getmembers(module, inspect.isclass):
                if hasattr(obj, "metadata") and hasattr(obj, "create_fitter") and obj != BasePlugin:

                    self.register_plugin(obj)
                    return True

        except (OSError, ImportError, AttributeError, TypeError) as e:
            self.logger.error(f"Failed to load plugin from {plugin_file}: {e}")

        return False


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry instance."""
    if not hasattr(get_plugin_registry, "_cache"):
        get_plugin_registry._cache = PluginRegistry()  # type: ignore[attr-defined]

    return get_plugin_registry._cache  # type: ignore[attr-defined, no-any-return]


def register_plugin(plugin_class: type[PluginInterface]) -> bool:
    """Convenience function to register a plugin globally."""
    return get_plugin_registry().register_plugin(plugin_class)


# Decorator for easy plugin registration
def prompt_fitting_plugin(
    name: str,
    version: str,
    description: str,
    author: str,
    priority: PluginPriority = PluginPriority.NORMAL,
    **metadata_kwargs: Any,
) -> Callable[[type[PluginInterface]], type[PluginInterface]]:
    """Decorator for registering prompt fitting plugins.

    Usage:
        @prompt_fitting_plugin(
            name="my_custom_fitter",
            version="1.0.0",
            description="Custom fitting strategy",
            author="Developer Name"
        )
        class MyCustomPlugin(BasePlugin):
            ...
    """

    def decorator(plugin_class: type[PluginInterface]) -> type[PluginInterface]:
        # Parse metadata kwargs into proper groups
        dependencies_kwargs = {}
        capabilities_kwargs = {}
        flags_kwargs = {}

        dependencies_keys = {"dependencies", "conflicts", "min_python_version"}
        capabilities_keys = {
            "supported_content_types",
            "max_token_limit",
            "requires_validation",
            "data_integrity_certified",
        }
        flags_keys = {"experimental", "deprecated"}

        for key, value in metadata_kwargs.items():
            if key in dependencies_keys:
                dependencies_kwargs[key] = value
            elif key in capabilities_keys:
                capabilities_kwargs[key] = value
            elif key in flags_keys:
                flags_kwargs[key] = value
            # Tags handled separately below

        # Extract tags if present
        tags = metadata_kwargs.get("tags", [])

        # Add metadata to the class
        setattr(
            plugin_class,
            "_plugin_metadata",
            PluginMetadata(
                info=PluginInfo(
                    name=name, version=version, description=description, author=author, tags=tags
                ),
                priority=priority,
                dependency_info=PluginDependencies(**dependencies_kwargs),
                capabilities=PluginCapabilities(**capabilities_kwargs),
                flags=PluginFlags(**flags_kwargs),
            ),
        )

        # Auto-register if possible
        try:
            register_plugin(plugin_class)
        except (TypeError, ValueError, AttributeError, ImportError) as e:
            warnings.warn(f"Failed to auto-register plugin {name}: {e}")

        return plugin_class

    return decorator
