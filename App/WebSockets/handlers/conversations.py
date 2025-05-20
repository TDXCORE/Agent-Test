"""
Handler para operaciones de conversaciones vía WebSocket.
"""

from typing import Dict, Any, List, Optional
import logging
from .base import BaseHandler
from ..events.dispatcher import dispatch_event
from App.DB.db_operations import (
    get_conversations_by_user,
    get_conversation_by_id,
    create_conversation,
    update_conversation,
    delete_conversation
)

logger = logging.getLogger(__name__)

class ConversationsHandler(BaseHandler):
    """Handler para operaciones de conversaciones."""
    
    def _register_actions(self) -> None:
        """Registra los manejadores de acciones para conversaciones."""
        self.action_handlers = {
            "get_all": self.get_all_conversations,
            "get_by_id": self.get_conversation,
            "create": self.create_conversation,
            "update": self.update_conversation,
            "delete": self.delete_conversation
        }
    
    async def get_all_conversations(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene todas las conversaciones de un usuario."""
        user_id = payload.get("user_id")
        
        if not user_id:
            raise ValueError("Se requiere user_id para obtener conversaciones")
        
        # Obtener conversaciones de la base de datos
        conversations = await get_conversations_by_user(user_id)
        
        return {
            "conversations": conversations
        }
    
    async def get_conversation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene una conversación por su ID."""
        conversation_id = payload.get("conversation_id")
        
        if not conversation_id:
            raise ValueError("Se requiere conversation_id para obtener conversación")
        
        # Obtener conversación de la base de datos
        conversation = await get_conversation_by_id(conversation_id)
        
        if not conversation:
            raise ValueError(f"Conversación no encontrada: {conversation_id}")
        
        return {
            "conversation": conversation
        }
    
    async def create_conversation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una nueva conversación."""
        conversation_data = payload.get("conversation")
        
        if not conversation_data:
            raise ValueError("Se requieren datos de conversación para crear")
        
        # Crear conversación en la base de datos
        new_conversation = await create_conversation(conversation_data)
        
        # Notificar a los clientes sobre la nueva conversación
        await dispatch_event("conversation_created", {
            "conversation": new_conversation
        })
        
        return {
            "conversation": new_conversation
        }
    
    async def update_conversation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza una conversación existente."""
        conversation_id = payload.get("conversation_id")
        conversation_data = payload.get("conversation")
        
        if not conversation_id:
            raise ValueError("Se requiere conversation_id para actualizar")
        
        if not conversation_data:
            raise ValueError("Se requieren datos de conversación para actualizar")
        
        # Actualizar conversación en la base de datos
        updated_conversation = await update_conversation(conversation_id, conversation_data)
        
        # Notificar a los clientes sobre la actualización
        await dispatch_event("conversation_updated", {
            "conversation_id": conversation_id,
            "conversation": updated_conversation
        })
        
        return {
            "conversation": updated_conversation
        }
    
    async def delete_conversation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Elimina una conversación."""
        conversation_id = payload.get("conversation_id")
        
        if not conversation_id:
            raise ValueError("Se requiere conversation_id para eliminar")
        
        # Eliminar conversación de la base de datos
        success = await delete_conversation(conversation_id)
        
        if success:
            # Notificar a los clientes sobre la eliminación
            await dispatch_event("conversation_deleted", {
                "conversation_id": conversation_id
            })
        
        return {
            "success": success,
            "conversation_id": conversation_id
        }
