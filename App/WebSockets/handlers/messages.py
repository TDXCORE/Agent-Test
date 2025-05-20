"""
Handler para operaciones de mensajes vía WebSocket.
"""

from typing import Dict, Any, List, Optional
import logging
from .base import BaseHandler
from ..events.dispatcher import dispatch_event
from App.DB.db_operations import (
    get_conversation_messages,
    add_message,
    get_conversation_history,
    mark_messages_as_read
)
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

class MessagesHandler(BaseHandler):
    """Handler para operaciones de mensajes."""
    
    def _register_actions(self) -> None:
        """Registra los manejadores de acciones para mensajes."""
        self.action_handlers = {
            "get_by_conversation": self.get_messages_by_conversation,
            "get_by_id": self.get_message,
            "create": self.create_message,
            "update": self.update_message,
            "delete": self.delete_message
        }
    
    # Función auxiliar para convertir funciones síncronas en asíncronas
    def to_async(self, func):
        @wraps(func)
        async def run(*args, **kwargs):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        return run
    
    async def get_messages_by_conversation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene todos los mensajes de una conversación."""
        conversation_id = payload.get("conversation_id")
        
        if not conversation_id:
            raise ValueError("Se requiere conversation_id para obtener mensajes")
        
        # Obtener mensajes de la base de datos
        messages = await self.to_async(get_conversation_messages)(conversation_id)
        
        # Parámetros opcionales de paginación
        limit = payload.get("limit", 50)
        offset = payload.get("offset", 0)
        
        # Aplicar paginación en memoria (no ideal, pero funciona para esta implementación inicial)
        paginated_messages = messages[offset:offset+limit] if messages else []
        
        return {
            "messages": paginated_messages,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(messages)
            }
        }
    
    async def get_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene un mensaje por su ID."""
        message_id = payload.get("message_id")
        conversation_id = payload.get("conversation_id")
        
        if not message_id or not conversation_id:
            raise ValueError("Se requiere message_id y conversation_id para obtener mensaje")
        
        # Obtener todos los mensajes de la conversación
        messages = await self.to_async(get_conversation_messages)(conversation_id)
        
        # Buscar el mensaje por ID
        message = next((m for m in messages if m.get("id") == message_id), None)
        
        if not message:
            raise ValueError(f"Mensaje no encontrado: {message_id}")
        
        return {
            "message": message
        }
    
    async def create_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo mensaje."""
        message_data = payload.get("message")
        
        if not message_data:
            raise ValueError("Se requieren datos de mensaje para crear")
        
        # Validar que tenga conversation_id
        conversation_id = message_data.get("conversation_id")
        if not conversation_id:
            raise ValueError("El mensaje debe tener conversation_id")
        
        # Extraer datos del mensaje
        role = message_data.get("role", "user")
        content = message_data.get("content")
        if not content:
            raise ValueError("El mensaje debe tener contenido")
        
        message_type = message_data.get("message_type", "text")
        media_url = message_data.get("media_url")
        external_id = message_data.get("external_id")
        read = message_data.get("read", False)
        
        # Crear mensaje en la base de datos
        new_message = await self.to_async(add_message)(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_type=message_type,
            media_url=media_url,
            external_id=external_id,
            read=read
        )
        
        # Notificar a los clientes sobre el nuevo mensaje
        await dispatch_event("new_message", {
            "conversation_id": conversation_id,
            "message": new_message
        })
        
        return {
            "message": new_message
        }
    
    async def update_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza un mensaje existente."""
        message_id = payload.get("message_id")
        conversation_id = payload.get("conversation_id")
        
        if not message_id or not conversation_id:
            raise ValueError("Se requiere message_id y conversation_id para actualizar")
        
        # En esta implementación inicial, solo podemos marcar mensajes como leídos
        # No hay una función específica para actualizar un mensaje individual
        count = await self.to_async(mark_messages_as_read)(conversation_id)
        
        # Notificar a los clientes sobre la actualización
        await dispatch_event("messages_read", {
            "conversation_id": conversation_id,
            "count": count
        })
        
        return {
            "success": True,
            "count": count
        }
    
    async def delete_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Elimina un mensaje."""
        message_id = payload.get("message_id")
        conversation_id = payload.get("conversation_id")
        
        if not message_id or not conversation_id:
            raise ValueError("Se requiere message_id y conversation_id para eliminar")
        
        # En esta implementación inicial, no podemos eliminar mensajes
        # Devolvemos un error
        raise ValueError("La eliminación de mensajes no está implementada")
