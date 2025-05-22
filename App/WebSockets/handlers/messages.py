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
    mark_messages_as_read,
    update_message,
    delete_message,
    get_message_by_id
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
        
        if not message_id:
            raise ValueError("Se requiere message_id para obtener mensaje")
        
        # Obtener mensaje directamente por ID
        message = await self.to_async(get_message_by_id)(message_id)
        
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
        message_data = payload.get("message")
        conversation_id = payload.get("conversation_id")
        mark_as_read = payload.get("mark_as_read", False)
        
        if not message_id:
            raise ValueError("Se requiere message_id para actualizar")
        
        # Si se solicita marcar como leído toda la conversación
        if mark_as_read and conversation_id:
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
        
        # Si se proporcionan datos para actualizar un mensaje específico
        if message_data:
            updated_message = await self.to_async(update_message)(message_id, message_data)
            
            # Obtener conversation_id del mensaje actualizado si no se proporcionó
            if not conversation_id and updated_message:
                conversation_id = updated_message.get("conversation_id")
            
            # Notificar a los clientes sobre la actualización
            if conversation_id:
                await dispatch_event("message_updated", {
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "message": updated_message
                })
            
            return {
                "message": updated_message
            }
        
        raise ValueError("Se requieren datos para actualizar el mensaje")
    
    async def delete_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Elimina un mensaje."""
        message_id = payload.get("message_id")
        conversation_id = payload.get("conversation_id")
        
        if not message_id:
            raise ValueError("Se requiere message_id para eliminar")
        
        # Si no se proporcionó conversation_id, obtener el mensaje primero
        if not conversation_id:
            message = await self.to_async(get_message_by_id)(message_id)
            if message:
                conversation_id = message.get("conversation_id")
        
        # Eliminar el mensaje
        success = await self.to_async(delete_message)(message_id)
        
        if success and conversation_id:
            # Notificar a los clientes sobre la eliminación
            await dispatch_event("message_deleted", {
                "conversation_id": conversation_id,
                "message_id": message_id
            })
        
        return {
            "success": success,
            "message_id": message_id
        }
