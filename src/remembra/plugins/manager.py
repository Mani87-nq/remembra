"""Plugin manager — registration, lifecycle, and hook dispatch.

The ``PluginManager`` maintains an ordered list of active plugins and
dispatches events to their hook methods.  Hooks are called in
registration order; each hook receives the event returned by the
previous hook (pipeline pattern), so plugins can compose.

Usage
-----
::

    manager = PluginManager()
    manager.register(MyPlugin(config={"key": "val"}))

    # Dispatch a store event
    event = MemoryEvent(memory_id="...", content="...", ...)
    event = await manager.dispatch_store(event)
"""

from __future__ import annotations

import logging
from typing import Any

from remembra.plugins.base import (
    ConflictEvent,
    EntityEvent,
    MemoryEvent,
    RecallEvent,
    RemembraPlugin,
)

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages plugin registration and hook dispatch."""

    def __init__(self) -> None:
        self._plugins: list[RemembraPlugin] = []
        self._registry: dict[str, type[RemembraPlugin]] = {}

    # -----------------------------------------------------------------------
    # Registration
    # -----------------------------------------------------------------------

    async def register(self, plugin: RemembraPlugin) -> None:
        """Register and activate a plugin instance.

        Raises:
            ValueError: If a plugin with the same name is already registered.
        """
        for existing in self._plugins:
            if existing.name == plugin.name:
                raise ValueError(f"Plugin '{plugin.name}' is already registered")

        try:
            await plugin.on_activate()
        except Exception as e:
            logger.error("Plugin activation failed: %s — %s", plugin.name, e)
            raise

        self._plugins.append(plugin)
        logger.info(
            "Plugin registered: %s v%s (%s)",
            plugin.name,
            plugin.version,
            plugin.description,
        )

    async def unregister(self, name: str) -> bool:
        """Deactivate and remove a plugin by name."""
        for i, plugin in enumerate(self._plugins):
            if plugin.name == name:
                try:
                    await plugin.on_deactivate()
                except Exception as e:
                    logger.warning("Plugin deactivation error: %s — %s", name, e)
                self._plugins.pop(i)
                logger.info("Plugin unregistered: %s", name)
                return True
        return False

    def register_class(self, cls: type[RemembraPlugin]) -> None:
        """Register a plugin class in the global registry (for marketplace).

        Does **not** instantiate or activate the plugin — call ``register()``
        with an instance for that.
        """
        name = cls.name
        self._registry[name] = cls
        logger.debug("Plugin class registered in marketplace: %s", name)

    # -----------------------------------------------------------------------
    # Query
    # -----------------------------------------------------------------------

    def list_plugins(self) -> list[dict[str, Any]]:
        """List all active plugins."""
        return [p.to_dict() for p in self._plugins]

    def get_plugin(self, name: str) -> RemembraPlugin | None:
        """Get an active plugin by name."""
        for plugin in self._plugins:
            if plugin.name == name:
                return plugin
        return None

    def list_registry(self) -> list[dict[str, Any]]:
        """List all registered plugin classes (marketplace catalog)."""
        return [
            {
                "name": cls.name,
                "version": cls.version,
                "description": cls.description,
                "author": cls.author,
            }
            for cls in self._registry.values()
        ]

    @property
    def count(self) -> int:
        return len(self._plugins)

    # -----------------------------------------------------------------------
    # Hook dispatch (pipeline pattern)
    # -----------------------------------------------------------------------

    async def dispatch_store(self, event: MemoryEvent) -> MemoryEvent:
        """Run the on_store pipeline across all enabled plugins."""
        for plugin in self._plugins:
            if not plugin.enabled:
                continue
            try:
                event = await plugin.on_store(event)
            except Exception as e:
                logger.warning(
                    "Plugin on_store failed: %s — %s",
                    plugin.name,
                    e,
                )
        return event

    async def dispatch_recall(self, event: RecallEvent) -> RecallEvent:
        """Run the on_recall pipeline across all enabled plugins."""
        for plugin in self._plugins:
            if not plugin.enabled:
                continue
            try:
                event = await plugin.on_recall(event)
            except Exception as e:
                logger.warning(
                    "Plugin on_recall failed: %s — %s",
                    plugin.name,
                    e,
                )
        return event

    async def dispatch_delete(self, event: MemoryEvent) -> MemoryEvent:
        """Run the on_delete pipeline across all enabled plugins."""
        for plugin in self._plugins:
            if not plugin.enabled:
                continue
            try:
                event = await plugin.on_delete(event)
            except Exception as e:
                logger.warning(
                    "Plugin on_delete failed: %s — %s",
                    plugin.name,
                    e,
                )
        return event

    async def dispatch_entity(self, event: EntityEvent) -> EntityEvent:
        """Run the on_entity pipeline across all enabled plugins."""
        for plugin in self._plugins:
            if not plugin.enabled:
                continue
            try:
                event = await plugin.on_entity(event)
            except Exception as e:
                logger.warning(
                    "Plugin on_entity failed: %s — %s",
                    plugin.name,
                    e,
                )
        return event

    async def dispatch_conflict(self, event: ConflictEvent) -> ConflictEvent:
        """Run the on_conflict pipeline across all enabled plugins."""
        for plugin in self._plugins:
            if not plugin.enabled:
                continue
            try:
                event = await plugin.on_conflict(event)
            except Exception as e:
                logger.warning(
                    "Plugin on_conflict failed: %s — %s",
                    plugin.name,
                    e,
                )
        return event

    # -----------------------------------------------------------------------
    # Shutdown
    # -----------------------------------------------------------------------

    async def shutdown(self) -> None:
        """Deactivate all plugins (called on app shutdown)."""
        for plugin in reversed(self._plugins):
            try:
                await plugin.on_deactivate()
            except Exception as e:
                logger.warning("Plugin shutdown error: %s — %s", plugin.name, e)
        self._plugins.clear()
        logger.info("All plugins shut down")
