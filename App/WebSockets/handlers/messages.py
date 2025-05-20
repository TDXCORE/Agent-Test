"""
Handler para operaciones de mensajes vía WebSocket.
"""

from typing import Dict, Any, List, Optional
import logging
from .base import BaseHandler
from ..events.dispatcher import dispatch_event
from App.DB.db_operations import (
    get_messages_by_conversation,
    get_message_by_id,
    create_message,
    update_message,
    delete_message
)

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
    
    async def get_messages_by_conversation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene todos los mensajes de una conversación."""
        conversation_id = payload.get("conversation_id")
        
        if not conversation_id:
            raise ValueError("Se requiere conversation_id para obtener mensajes")
        
        # Parámetros opcionales de paginación
        limit = payload.get("limit", 50)
        offset = payload.get("offset", 0)
        
        # Obtener mensajes de la base de datos
        messages = await get_messages_by_conversation(conversation_id, limit, offset)
        
        return {
            "messages": messages,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(messages)  # Esto debería ser el total real, no solo los recuperados
            }
        }
    
    async def get_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene un mensaje por su ID."""
        message_id = payload.get("message_id")
        
        if not message_id:
            raise ValueError("Se requiere message_id para obtener mensaje")
        
        # Obtener mensaje de la base de datos
        message = await get_message_by_id(message_id)
        
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
        if "conversation_id" not in message_data:
            raise ValueError("El mensaje debe tener conversation_id")
        
        # Crear mensaje en la base de datos
        new_message = await create_message(message_data)
        
        # Notificar a los clientes sobre el nuevo mensaje
        await dispatch_event("new_message", {
            "conversation_id": new_message["conversation_id"],
            "message": new_message
        })
        
        return {
            "message": new_message
        }
    
    async def update_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza un mensaje existente."""
        message_id = payload.get("message_id")
        message_data = payload.get("message")
        
        if not message_id:
            raise ValueError("Se requiere message_id para actualizar")
        
        if not message_data:
            raise ValueError("Se requieren datos de mensaje para actualizar")
        
        # Obtener mensaje actual para conocer su conversation_id
        current_message = await get_message_by_id(message_id)
        if not current_message:
            raise ValueError(f"Mensaje no encontrado: {message_id}")
        
        # Actualizar mensaje en la base de datos
        updated_message = await update_message(message_id, message_data)
        
        # Notificar a los clientes sobre la actualización
        await dispatch_event("message_updated", {
            "conversation_id": current_message["conversation_id"],
            "message_id": message_id,
            "message": updated_message
        })
        
        return {
            "message": updated_message
        }
    
    async def delete_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Elimina un mensaje."""
        message_id = payload.get("message_id")
        
        if not message_id:
            raise ValueError("Se requiere message_id para eliminar")
        
        # Obtener mensaje actual para conocer su conversation_id
        current_message = await get_message_by_id(message_id)
        if not current_message:
            raise ValueError(f"Mensaje no encontrado: {message_id}")
        
        # Eliminar mensaje de la base de datos
        success = await delete_message(message_id)
        
        if success:
            # Notificar a los clientes sobre la eliminación
            await dispatch_event("message_deleted", {
                "conversation_id": current_message["conversation_id"],
                "message_id": message_id
            })
        
        return {
            "success": success,
            "message_id": message_id
        }
