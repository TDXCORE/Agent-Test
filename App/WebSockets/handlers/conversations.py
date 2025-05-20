"""
Handler para operaciones de conversaciones vía WebSocket.
"""

from typing import Dict, Any, List, Optional
import logging
from .base import BaseHandler
from ..events.dispatcher import dispatch_event
from App.DB.db_operations import (
    get_active_conversation,
    create_conversation,
    close_conversation,
    get_or_create_conversation,
    get_user_by_id
)
import asyncio
from functools import wraps

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
    
    # Función auxiliar para convertir funciones síncronas en asíncronas
    def to_async(self, func):
        @wraps(func)
        async def run(*args, **kwargs):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        return run
    
    async def get_all_conversations(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene todas las conversaciones de un usuario."""
        user_id = payload.get("user_id")
        
        if not user_id:
            raise ValueError("Se requiere user_id para obtener conversaciones")
        
        # Verificar que el usuario existe
        user = await self.to_async(get_user_by_id)(user_id)
        if not user:
            raise ValueError(f"Usuario no encontrado: {user_id}")
        
        # En esta implementación inicial, solo devolvemos la conversación activa
        # En una implementación completa, se debería consultar todas las conversaciones del usuario
        external_id = user.get("phone") or user.get("email")
        if not external_id:
            return {"conversations": []}
        
        conversation = await self.to_async(get_active_conversation)(external_id)
        
        return {
            "conversations": [conversation] if conversation else []
        }
    
    async def get_conversation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene una conversación por su ID."""
        conversation_id = payload.get("conversation_id")
        external_id = payload.get("external_id")
        
        if not conversation_id and not external_id:
            raise ValueError("Se requiere conversation_id o external_id para obtener conversación")
        
        # Obtener conversación de la base de datos
        conversation = None
        if conversation_id:
            # Aquí deberíamos tener una función para obtener por ID
            # Como no existe, usamos un enfoque alternativo
            raise ValueError("Búsqueda por ID no implementada aún")
        elif external_id:
            conversation = await self.to_async(get_active_conversation)(external_id)
        
        if not conversation:
            raise ValueError(f"Conversación no encontrada")
        
        return {
            "conversation": conversation
        }
    
    async def create_conversation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una nueva conversación."""
        user_id = payload.get("user_id")
        external_id = payload.get("external_id")
        platform = payload.get("platform", "whatsapp")
        
        if not user_id or not external_id:
            raise ValueError("Se requieren user_id y external_id para crear conversación")
        
        # Crear conversación en la base de datos
        new_conversation = await self.to_async(create_conversation)(user_id, external_id, platform)
        
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
        
        if not conversation_id:
            raise ValueError("Se requiere conversation_id para actualizar")
        
        # En esta implementación inicial, solo podemos cerrar conversaciones
        # En una implementación completa, se deberían soportar más operaciones
        updated_conversation = await self.to_async(close_conversation)(conversation_id)
        
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
        
        # En esta implementación inicial, no podemos eliminar conversaciones
        # En su lugar, las cerramos
        closed_conversation = await self.to_async(close_conversation)(conversation_id)
        success = closed_conversation is not None
        
        if success:
            # Notificar a los clientes sobre la "eliminación" (cierre)
            await dispatch_event("conversation_deleted", {
                "conversation_id": conversation_id
            })
        
        return {
            "success": success,
            "conversation_id": conversation_id
        }
