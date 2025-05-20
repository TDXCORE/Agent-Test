"""
Modelos base para mensajes WebSocket.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from datetime import datetime

class MessageType(str, Enum):
    """Tipos de mensajes WebSocket."""
    # Mensajes del cliente al servidor
    CONNECT = "connect"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    REQUEST = "request"
    
    # Mensajes del servidor al cliente
    CONNECTED = "connected"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    RESPONSE = "response"
    ERROR = "error"
    EVENT = "event"

class WebSocketMessage(BaseModel):
    """Modelo base para todos los mensajes WebSocket."""
    type: MessageType
    id: str = Field(..., description="Identificador único del mensaje")
    timestamp: datetime = Field(default_factory=datetime.now)
    payload: Dict[str, Any] = Field(default_factory=dict)

class ErrorResponse(BaseModel):
    """Modelo para respuestas de error."""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class SubscriptionRequest(BaseModel):
    """Modelo para solicitudes de suscripción."""
    resource: str
    filters: Optional[Dict[str, Any]] = None

class ResourceRequest(BaseModel):
    """Modelo para solicitudes de recursos."""
    resource: str
    action: str
    data: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    pagination: Optional[Dict[str, Any]] = None
