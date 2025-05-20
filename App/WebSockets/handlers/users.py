"""
Handler para operaciones de usuarios vía WebSocket.
"""

from typing import Dict, Any, List, Optional
import logging
from .base import BaseHandler
from ..events.dispatcher import dispatch_event
from App.DB.db_operations import (
    get_all_users,
    get_user_by_id,
    create_user,
    update_user,
    delete_user
)

logger = logging.getLogger(__name__)

class UsersHandler(BaseHandler):
    """Handler para operaciones de usuarios."""
    
    def _register_actions(self) -> None:
        """Registra los manejadores de acciones para usuarios."""
        self.action_handlers = {
            "get_all": self.get_all_users,
            "get_by_id": self.get_user,
            "create": self.create_user,
            "update": self.update_user,
            "delete": self.delete_user
        }
    
    async def get_all_users(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene todos los usuarios."""
        # Parámetros opcionales de paginación
        limit = payload.get("limit", 50)
        offset = payload.get("offset", 0)
        
        # Obtener usuarios de la base de datos
        users = await get_all_users(limit, offset)
        
        return {
            "users": users,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(users)  # Esto debería ser el total real, no solo los recuperados
            }
        }
    
    async def get_user(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene un usuario por su ID."""
        user_id = payload.get("user_id")
        
        if not user_id:
            raise ValueError("Se requiere user_id para obtener usuario")
        
        # Obtener usuario de la base de datos
        user = await get_user_by_id(user_id)
        
        if not user:
            raise ValueError(f"Usuario no encontrado: {user_id}")
        
        return {
            "user": user
        }
    
    async def create_user(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Crea un nuevo usuario."""
        user_data = payload.get("user")
        
        if not user_data:
            raise ValueError("Se requieren datos de usuario para crear")
        
        # Crear usuario en la base de datos
        new_user = await create_user(user_data)
        
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
        
        # Actualizar usuario en la base de datos
        updated_user = await update_user(user_id, user_data)
        
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
        
        # Eliminar usuario de la base de datos
        success = await delete_user(user_id)
        
        if success:
            # Notificar a los clientes sobre la eliminación
            await dispatch_event("user_deleted", {
                "user_id": user_id
            })
        
        return {
            "success": success,
            "user_id": user_id
        }
