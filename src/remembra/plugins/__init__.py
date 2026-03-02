"""Remembra plugin system.

Plugins hook into the memory lifecycle to extend or modify behaviour.
Supported hooks:

- ``on_store``      — called after a memory is stored
- ``on_recall``     — called after recall results are assembled
- ``on_delete``     — called when a memory is deleted
- ``on_entity``     — called when a new entity is created or merged
- ``on_conflict``   — called when a memory conflict is detected

Plugins are registered via the ``PluginManager`` and invoked in
registration order.
"""
