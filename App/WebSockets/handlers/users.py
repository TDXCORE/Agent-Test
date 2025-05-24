"""
Handler para operaciones de usuarios vía WebSocket.
"""

from typing import Dict, Any, List, Optional
import logging
from .base import BaseHandler
from ..events.dispatcher import dispatch_event
from App.DB.db_operations import (
    get_user_by_phone,
    get_user_by_email,
    get_user_by_id,
    create_user,
    update_user,
    get_or_create_user,
    get_all_users_from_db,
    delete_user
)
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

class UsersHandler(BaseHandler):
    """Handler para operaciones de usuarios."""
    
    def _register_actions(self) -> None:
        """Registra los manejadores de acciones para usuarios."""
        self.action_handlers = {
            "get_all_users": self.get_all_users,
            "get_user_by_id": self.get_user,
            "create_user": self.create_user,
            "update_user": self.update_user,
            "delete_user": self.delete_user,
            "get_all_with_stats": self.get_all_users_with_stats,
            "get_profile": self.get_user_profile,
            "search": self.search_users
        }
    
    # Función auxiliar para convertir funciones síncronas en asíncronas
    def to_async(self, func):
        @wraps(func)
        async def run(*args, **kwargs):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        return run
    
    async def get_all_users(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene todos los usuarios."""
        phone = payload.get("phone")
        email = payload.get("email")
        get_all = payload.get("get_all", False)
        
        users = []
        
        if phone:
            user = await self.to_async(get_user_by_phone)(phone)
            if user:
                users.append(user)
        elif email:
            user = await self.to_async(get_user_by_email)(email)
            if user:
                users.append(user)
        else:
            # Sin criterios de búsqueda, obtenemos todos los usuarios
            users = await self.to_async(get_all_users_from_db)()
            logger.info(f"Obtenidos {len(users)} usuarios de la base de datos")
        
        return {
            "users": users,
            "total": len(users)
        }
    
    async def get_user(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene un usuario por su ID, teléfono o email."""
        user_id = payload.get("user_id")
        phone = payload.get("phone")
        email = payload.get("email")
        
        if not user_id and not phone and not email:
            raise ValueError("Se requiere user_id, phone o email para obtener usuario")
        
        # Obtener usuario de la base de datos
        user = None
        
        if user_id:
            user = await self.to_async(get_user_by_id)(user_id)
        elif phone:
            user = await self.to_async(get_user_by_phone)(phone)
        elif email:
            user = await self.to_async(get_user_by_email)(email)
        
        if not user:
            raise ValueError(f"Usuario no encontrado")
        
        return {
            "user": user
        }
    
    async def create_user(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo usuario."""
        user_data = payload.get("user")
        
        if not user_data:
            raise ValueError("Se requieren datos de usuario para crear")
        
        # Validar datos mínimos
        if not user_data.get("phone") and not user_data.get("email"):
            raise ValueError("Se requiere al menos phone o email para crear usuario")
        
        # Crear usuario en la base de datos
        new_user = await self.to_async(create_user)(user_data)
        
        # Notificar a los clientes sobre el nuevo usuario
        await dispatch_event("user_created", {
            "user": new_user
        })
        
        return {
            "user": new_user
        }
    
    async def update_user(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza un usuario existente."""
        user_id = payload.get("user_id")
        user_data = payload.get("user")
        
        if not user_id:
            raise ValueError("Se requiere user_id para actualizar")
        
        if not user_data:
            raise ValueError("Se requieren datos de usuario para actualizar")
        
        # Verificar que el usuario existe
        existing_user = await self.to_async(get_user_by_id)(user_id)
        if not existing_user:
            raise ValueError(f"Usuario no encontrado: {user_id}")
        
        # Actualizar usuario en la base de datos
        updated_user = await self.to_async(update_user)(user_id, user_data)
        
        # Notificar a los clientes sobre la actualización
        await dispatch_event("user_updated", {
            "user_id": user_id,
            "user": updated_user
        })
        
        return {
            "user": updated_user
        }
    
    async def delete_user(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Elimina un usuario."""
        user_id = payload.get("user_id")
        
        if not user_id:
            raise ValueError("Se requiere user_id para eliminar")
        
        # Verificar que el usuario existe
        existing_user = await self.to_async(get_user_by_id)(user_id)
        if not existing_user:
            raise ValueError(f"Usuario no encontrado: {user_id}")
        
        # Eliminar usuario (marcar como inactivo)
        success = await self.to_async(delete_user)(user_id)
        
        if success:
            # Notificar a los clientes sobre la eliminación
            await dispatch_event("user_deleted", {
                "user_id": user_id
            })
        
        return {
            "success": success,
            "user_id": user_id
        }
    
    async def get_all_users_with_stats(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene todos los usuarios con estadísticas."""
        limit = payload.get("limit", 50)
        offset = payload.get("offset", 0)
        
        # Obtener usuarios con estadísticas
        users_with_stats = await self.to_async(self._get_all_users_with_stats)(limit, offset)
        
        return {
            "users": users_with_stats,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(users_with_stats)
            }
        }
    
    async def get_user_profile(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene el perfil completo de un usuario."""
        user_id = payload.get("user_id")
        
        if not user_id:
            raise ValueError("Se requiere user_id")
        
        # Obtener perfil completo del usuario
        user_profile = await self.to_async(self._get_user_profile)(user_id)
        
        if not user_profile:
            raise ValueError(f"Usuario no encontrado: {user_id}")
        
        return {
            "user_profile": user_profile
        }
    
    async def search_users(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Busca usuarios por teléfono, email o nombre."""
        search_term = payload.get("search_term")
        limit = payload.get("limit", 50)
        offset = payload.get("offset", 0)
        
        if not search_term:
            raise ValueError("Se requiere search_term")
        
        # Buscar usuarios
        users = await self.to_async(self._search_users)(search_term, limit, offset)
        
        return {
            "users": users,
            "search_term": search_term,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(users)
            }
        }
    
    def _get_all_users_with_stats(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Función auxiliar para obtener usuarios con estadísticas."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Consulta compleja con JOINs para obtener estadísticas
        response = supabase.rpc('get_users_with_stats', {
            'limit_param': limit,
            'offset_param': offset
        }).execute()
        
        # Si la función RPC no existe, usar consulta alternativa
        if not response.data:
            # Consulta alternativa usando múltiples queries
            users_response = supabase.table("users").select("*").range(offset, offset + limit - 1).execute()
            users = users_response.data if users_response.data else []
            
            # Agregar estadísticas manualmente
            for user in users:
                user_id = user["id"]
                
                # Contar conversaciones
                conv_response = supabase.table("conversations").select("id").eq("user_id", user_id).execute()
                user["conversation_count"] = len(conv_response.data) if conv_response.data else 0
                
                # Obtener último mensaje
                msg_response = supabase.table("messages").select("created_at").in_(
                    "conversation_id",
                    [c["id"] for c in conv_response.data] if conv_response.data else []
                ).order("created_at", desc=True).limit(1).execute()
                
                user["last_message_at"] = msg_response.data[0]["created_at"] if msg_response.data else None
            
            return users
        
        return response.data
    
    def _get_user_profile(self, user_id: str) -> Optional[Dict]:
        """Función auxiliar para obtener perfil completo del usuario."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Obtener usuario con todas las relaciones
        user_response = supabase.table("users").select("*").eq("id", user_id).execute()
        
        if not user_response.data:
            return None
        
        user = user_response.data[0]
        
        # Obtener conversaciones
        conv_response = supabase.table("conversations").select(
            "*, messages(content, created_at, role, message_type, read)"
        ).eq("user_id", user_id).execute()
        user["conversations"] = conv_response.data if conv_response.data else []
        
        # Obtener meetings
        meetings_response = supabase.table("meetings").select("*").eq("user_id", user_id).execute()
        user["meetings"] = meetings_response.data if meetings_response.data else []
        
        # Obtener lead qualification
        lead_response = supabase.table("lead_qualification").select("*").eq("user_id", user_id).execute()
        if lead_response.data:
            user["lead_qualification"] = lead_response.data[0]
            
            # Obtener BANT data
            bant_response = supabase.table("bant_data").select("*").eq(
                "lead_qualification_id", lead_response.data[0]["id"]
            ).execute()
            if bant_response.data:
                user["bant_data"] = bant_response.data[0]
            
            # Obtener requirements
            req_response = supabase.table("requirements").select(
                "*, features(*), integrations(*)"
            ).eq("lead_qualification_id", lead_response.data[0]["id"]).execute()
            if req_response.data:
                user["requirements"] = req_response.data[0]
        
        return user
    
    def _search_users(self, search_term: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Función auxiliar para buscar usuarios."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Buscar en múltiples campos
        response = supabase.table("users").select("*").or_(
            f"phone.ilike.%{search_term}%,"
            f"email.ilike.%{search_term}%,"
            f"full_name.ilike.%{search_term}%"
        ).range(offset, offset + limit - 1).execute()
        
        return response.data if response.data else []
