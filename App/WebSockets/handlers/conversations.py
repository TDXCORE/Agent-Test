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
    get_user_by_id,
    get_conversation_by_id,
    get_user_conversations,
    update_agent_status
)
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

class ConversationsHandler(BaseHandler):
    """Handler para operaciones de conversaciones."""
    
    def _register_actions(self) -> None:
        """Registra los manejadores de acciones para conversaciones."""
        self.action_handlers = {
            "get_all_conversations": self.get_all_conversations,
            "get_conversation_by_id": self.get_conversation,
            "create_conversation": self.create_conversation,
            "close_conversation": self.update_conversation,
            "update_agent_status": self.toggle_agent_status,
            "get_user_conversations": self.get_conversations_by_agent_status,
            "get_conversation_with_details": self.get_conversation_with_details,
            "archive_conversation": self.archive_conversation
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
        include_closed = payload.get("include_closed", False)
        
        if not user_id:
            raise ValueError("Se requiere user_id para obtener conversaciones")
        
        # Verificar que el usuario existe
        user = await self.to_async(get_user_by_id)(user_id)
        if not user:
            raise ValueError(f"Usuario no encontrado: {user_id}")
        
        # Obtener todas las conversaciones del usuario
        conversations = await self.to_async(get_user_conversations)(user_id, include_closed)
        
        return {
            "conversations": conversations
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
            conversation = await self.to_async(get_conversation_by_id)(conversation_id)
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
    
    async def toggle_agent_status(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Activa o desactiva el agente IA para una conversación."""
        conversation_id = payload.get("conversation_id")
        enabled = payload.get("enabled")
        
        if not conversation_id or enabled is None:
            raise ValueError("Se requieren conversation_id y enabled")
        
        # Actualizar estado del agente
        updated_conversation = await self.to_async(update_agent_status)(conversation_id, enabled)
        
        # Notificar a los clientes sobre el cambio
        await dispatch_event("agent_toggled", {
            "conversation_id": conversation_id,
            "agent_enabled": enabled,
            "conversation": updated_conversation
        })
        
        return {
            "conversation": updated_conversation,
            "agent_enabled": enabled
        }
    
    async def get_conversations_by_agent_status(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene conversaciones filtradas por estado del agente."""
        agent_enabled = payload.get("agent_enabled")
        user_id = payload.get("user_id")
        
        if agent_enabled is None:
            raise ValueError("Se requiere agent_enabled")
        
        # Obtener conversaciones filtradas por estado del agente
        conversations = await self.to_async(self._get_conversations_by_agent_status)(agent_enabled, user_id)
        
        # Log para debugging
        logger.info(f"Conversaciones obtenidas: {len(conversations)} (agent_enabled={agent_enabled})")
        if conversations:
            logger.info(f"Primera conversación de ejemplo: {conversations[0]}")
        
        return {
            "conversations": conversations,
            "agent_enabled": agent_enabled
        }
    
    async def get_conversation_with_details(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene una conversación con detalles completos."""
        conversation_id = payload.get("conversation_id")
        
        if not conversation_id:
            raise ValueError("Se requiere conversation_id")
        
        # Obtener conversación con detalles
        conversation_details = await self.to_async(self._get_conversation_with_details)(conversation_id)
        
        if not conversation_details:
            raise ValueError(f"Conversación no encontrada: {conversation_id}")
        
        return {
            "conversation": conversation_details
        }
    
    async def archive_conversation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Archiva una conversación."""
        conversation_id = payload.get("conversation_id")
        
        if not conversation_id:
            raise ValueError("Se requiere conversation_id")
        
        # Archivar conversación
        archived_conversation = await self.to_async(self._archive_conversation)(conversation_id)
        
        # Notificar a los clientes sobre el archivado
        await dispatch_event("conversation_archived", {
            "conversation_id": conversation_id,
            "conversation": archived_conversation
        })
        
        return {
            "conversation": archived_conversation,
            "archived": True
        }
    
    def _get_conversations_by_agent_status(self, agent_enabled: bool, user_id: Optional[str] = None) -> List[Dict]:
        """Función auxiliar para obtener conversaciones por estado del agente."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Consulta mejorada para incluir datos del usuario y último mensaje
        query = supabase.table("conversations").select(
            """
            *,
            users!inner(id, full_name, email, phone, company),
            messages(id, content, created_at, role, read)
            """
        ).eq("agent_enabled", agent_enabled)
        
        if user_id:
            query = query.eq("user_id", user_id)
        
        response = query.order("updated_at", desc=True).execute()
        
        # Procesar los datos para incluir información adicional
        conversations = response.data if response.data else []
        
        for conversation in conversations:
            # Procesar mensajes para obtener el último mensaje y contar no leídos
            messages = conversation.get("messages", [])
            if messages:
                # Ordenar mensajes por fecha
                messages.sort(key=lambda x: x["created_at"])
                conversation["last_message"] = messages[-1] if messages else None
                conversation["unread_count"] = len([m for m in messages if not m.get("read", False) and m.get("role") == "user"])
            else:
                conversation["last_message"] = None
                conversation["unread_count"] = 0
            
            # Asegurar que los datos del usuario estén disponibles
            user_data = conversation.get("users")
            if user_data:
                # Si users es una lista, tomar el primer elemento
                if isinstance(user_data, list) and len(user_data) > 0:
                    conversation["user"] = user_data[0]
                elif isinstance(user_data, dict):
                    conversation["user"] = user_data
                else:
                    conversation["user"] = None
            else:
                conversation["user"] = None
        
        return conversations
    
    def _get_conversation_with_details(self, conversation_id: str) -> Optional[Dict]:
        """Función auxiliar para obtener conversación con detalles."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Obtener conversación con usuario y último mensaje
        response = supabase.table("conversations").select(
            """
            *,
            users(full_name, email, phone, company),
            messages(content, created_at, role, message_type, read)
            """
        ).eq("id", conversation_id).execute()
        
        if not response.data:
            return None
        
        conversation = response.data[0]
        
        # Obtener lead qualification si existe
        lead_response = supabase.table("lead_qualification").select(
            "current_step"
        ).eq("conversation_id", conversation_id).execute()
        
        if lead_response.data:
            conversation["lead_step"] = lead_response.data[0]["current_step"]
        
        # Obtener último mensaje
        if conversation.get("messages"):
            messages = conversation["messages"]
            conversation["last_message"] = max(messages, key=lambda x: x["created_at"]) if messages else None
            conversation["unread_count"] = len([m for m in messages if not m["read"] and m["role"] == "user"])
        
        return conversation
    
    def _archive_conversation(self, conversation_id: str) -> Dict:
        """Función auxiliar para archivar conversación."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        update_data = {
            "status": "archived",
            "updated_at": "now()"
        }
        
        response = supabase.table("conversations").update(update_data).eq("id", conversation_id).execute()
        return response.data[0] if response.data else {}
