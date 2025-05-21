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
    get_all_users_from_db
)
import asyncio
from functools import wraps

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
        
        # En esta implementación inicial, no podemos eliminar usuarios
        # Devolvemos un error
        raise ValueError("La eliminación de usuarios no está implementada")
