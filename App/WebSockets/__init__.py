"""
Módulo WebSockets para reemplazar las APIs REST existentes.
Proporciona funcionalidad en tiempo real para conversaciones, mensajes y usuarios.
"""

from .setup import setup_websockets
from .connection import ConnectionManager

__all__ = ["setup_websockets", "ConnectionManager"]
