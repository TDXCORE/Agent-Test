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
            "get_all_messages": self.get_messages_by_conversation,
            "send_message": self.create_message,
            "get_conversation_messages": self.get_messages_by_conversation,
            "mark_as_read": self.mark_conversation_as_read,
            "delete_message": self.delete_message,
            "update_message": self.update_message
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
    
    async def send_to_whatsapp(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Envía mensaje a WhatsApp usando simple_webhook.py"""
        from App.Services.simple_webhook import send_whatsapp_message
        
        phone = payload.get("phone")
        message_type = payload.get("message_type", "text")
        content = payload.get("content")
        caption = payload.get("caption")
        
        if not phone or not content:
            raise ValueError("Se requieren phone y content")
        
        # Enviar mensaje
        result = await self.to_async(send_whatsapp_message)(phone, message_type, content, caption)
        
        # Guardar en BD si se especifica conversation_id
        conversation_id = payload.get("conversation_id")
        if conversation_id and result:
            new_message = await self.to_async(add_message)(
                conversation_id=conversation_id,
                role="assistant",
                content=content,
                message_type=message_type,
                read=True
            )
            
            # Notificar sobre el nuevo mensaje
            await dispatch_event("new_message", {
                "conversation_id": conversation_id,
                "message": new_message
            })
        
        return {"success": result is not None, "result": result}
    
    async def mark_conversation_as_read(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Marca todos los mensajes de una conversación como leídos."""
        conversation_id = payload.get("conversation_id")
        
        if not conversation_id:
            raise ValueError("Se requiere conversation_id")
        
        # Marcar mensajes como leídos
        count = await self.to_async(mark_messages_as_read)(conversation_id)
        
        # Notificar a los clientes
        await dispatch_event("messages_read", {
            "conversation_id": conversation_id,
            "count": count
        })
        
        return {
            "success": True,
            "conversation_id": conversation_id,
            "count": count
        }
    
    async def get_unread_count(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene el conteo de mensajes no leídos por conversación."""
        user_id = payload.get("user_id")
        conversation_id = payload.get("conversation_id")
        
        # Obtener conteo de mensajes no leídos
        unread_counts = await self.to_async(self._get_unread_count)(user_id, conversation_id)
        
        return {
            "unread_counts": unread_counts
        }
    
    async def search_messages(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Busca mensajes por contenido."""
        search_term = payload.get("search_term")
        conversation_id = payload.get("conversation_id")
        limit = payload.get("limit", 50)
        offset = payload.get("offset", 0)
        
        if not search_term:
            raise ValueError("Se requiere search_term")
        
        # Buscar mensajes
        messages = await self.to_async(self._search_messages)(search_term, conversation_id, limit, offset)
        
        return {
            "messages": messages,
            "search_term": search_term,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(messages)
            }
        }
    
    def _get_unread_count(self, user_id: Optional[str] = None, conversation_id: Optional[str] = None) -> List[Dict]:
        """Función auxiliar para obtener conteo de mensajes no leídos."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        query = supabase.table("messages").select(
            "conversation_id, count(*)"
        ).eq("read", False).eq("role", "user")
        
        if conversation_id:
            query = query.eq("conversation_id", conversation_id)
        elif user_id:
            # Filtrar por conversaciones del usuario
            query = query.in_(
                "conversation_id",
                supabase.table("conversations").select("id").eq("user_id", user_id).execute().data
            )
        
        response = query.execute()
        return response.data if response.data else []
    
    def _search_messages(self, search_term: str, conversation_id: Optional[str] = None, 
                        limit: int = 50, offset: int = 0) -> List[Dict]:
        """Función auxiliar para buscar mensajes."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        query = supabase.table("messages").select(
            "*, conversations(external_id, platform, users(full_name, phone))"
        ).ilike("content", f"%{search_term}%")
        
        if conversation_id:
            query = query.eq("conversation_id", conversation_id)
        
        response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        return response.data if response.data else []
