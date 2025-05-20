"""
Sistema de eventos para WebSockets.
"""

from .dispatcher import dispatch_event, register_listener

__all__ = ["dispatch_event", "register_listener"]
