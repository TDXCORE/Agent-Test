"""
Integración del módulo WebSockets con la aplicación principal.
"""

import logging
from fastapi import FastAPI, Depends, HTTPException
from typing import Dict, Any, Optional, List
from App.DB.db_operations import (
    get_user_by_id,
    create_user,
    update_user,
    get_active_conversation,
    create_conversation,
    close_conversation,
    get_conversation_messages,
    add_message,
    get_conversation_history
)

from .main import init_websockets, notify_event

logger = logging.getLogger(__name__)

def integrate_websockets(app: FastAPI):
    """
    Integra el módulo WebSockets con la aplicación principal.
    
    Esta función debe ser llamada desde el punto de entrada principal
    de la aplicación (App/api.py) para inicializar los WebSockets.
    """
    # Inicializar WebSockets en la aplicación FastAPI
    init_websockets(app)
    
    # Registrar middleware para notificar eventos desde las APIs REST
    register_event_middleware(app)
    
    logger.info("Módulo WebSockets integrado con la aplicación principal")

def register_event_middleware(app: FastAPI):
    """
    Registra middleware para notificar eventos desde las APIs REST.
    
    Esto permite que las operaciones realizadas a través de las APIs REST
    también notifiquen a los clientes WebSocket sobre los cambios.
    """
    # Middleware para conversaciones
    @app.middleware("http")
    async def conversation_events_middleware(request, call_next):
        # Procesar la solicitud normalmente
        response = await call_next(request)
        
        # Verificar si es una operación de conversación
        path = request.url.path
        method = request.method
        
        if "/api/conversations" in path:
            try:
                # Extraer ID de conversación de la URL si existe
                conversation_id = None
                parts = path.split("/")
                if len(parts) > 3 and parts[3].isalnum():
                    conversation_id = parts[3]
                
                # Notificar evento según la operación
                if method == "POST" and response.status_code == 201:
                    # Nueva conversación creada
                    body = await request.json()
                    await notify_event("conversation_created", {
                        "conversation": body
                    })
                
                elif method == "PUT" and conversation_id and response.status_code == 200:
                    # Conversación actualizada
                    body = await request.json()
                    await notify_event("conversation_updated", {
                        "conversation_id": conversation_id,
                        "conversation": body
                    })
                
                elif method == "DELETE" and conversation_id and response.status_code == 200:
                    # Conversación eliminada
                    await notify_event("conversation_deleted", {
                        "conversation_id": conversation_id
                    })
            
            except Exception as e:
                logger.error(f"Error en middleware de conversaciones: {str(e)}")
        
        return response
    
    # Middleware para mensajes
    @app.middleware("http")
    async def message_events_middleware(request, call_next):
        # Procesar la solicitud normalmente
        response = await call_next(request)
        
        # Verificar si es una operación de mensaje
        path = request.url.path
        method = request.method
        
        if "/api/messages" in path:
            try:
                # Extraer ID de mensaje de la URL si existe
                message_id = None
                parts = path.split("/")
                if len(parts) > 3 and parts[3].isalnum():
                    message_id = parts[3]
                
                # Notificar evento según la operación
                if method == "POST" and response.status_code == 201:
                    # Nuevo mensaje creado
                    body = await request.json()
                    conversation_id = body.get("conversation_id")
                    if conversation_id:
                        await notify_event("new_message", {
                            "conversation_id": conversation_id,
                            "message": body
                        })
                
                elif method == "PUT" and message_id and response.status_code == 200:
                    # Mensaje actualizado
                    body = await request.json()
                    conversation_id = body.get("conversation_id")
                    if conversation_id:
                        await notify_event("message_updated", {
                            "conversation_id": conversation_id,
                            "message_id": message_id,
                            "message": body
                        })
                
                elif method == "DELETE" and message_id and response.status_code == 200:
                    # Para el caso de eliminación, obtener el conversation_id de la URL
                    conversation_id = request.query_params.get("conversation_id")
                    if conversation_id:
                        await notify_event("message_deleted", {
                            "conversation_id": conversation_id,
                            "message_id": message_id
                        })
            
            except Exception as e:
                logger.error(f"Error en middleware de mensajes: {str(e)}")
        
        return response
    
    # Middleware para usuarios
    @app.middleware("http")
    async def user_events_middleware(request, call_next):
        # Procesar la solicitud normalmente
        response = await call_next(request)
        
        # Verificar si es una operación de usuario
        path = request.url.path
        method = request.method
        
        if "/api/users" in path:
            try:
                # Extraer ID de usuario de la URL si existe
                user_id = None
                parts = path.split("/")
                if len(parts) > 3 and parts[3].isalnum():
                    user_id = parts[3]
                
                # Notificar evento según la operación
                if method == "POST" and response.status_code == 201:
                    # Nuevo usuario creado
                    body = await request.json()
                    await notify_event("user_created", {
                        "user": body
                    })
                
                elif method == "PUT" and user_id and response.status_code == 200:
                    # Usuario actualizado
                    body = await request.json()
                    await notify_event("user_updated", {
                        "user_id": user_id,
                        "user": body
                    })
                
                elif method == "DELETE" and user_id and response.status_code == 200:
                    # Usuario eliminado
                    await notify_event("user_deleted", {
                        "user_id": user_id
                    })
            
            except Exception as e:
                logger.error(f"Error en middleware de usuarios: {str(e)}")
        
        return response

# Ejemplo de cómo integrar en App/api.py:
"""
from fastapi import FastAPI
from App.WebSockets.integration import integrate_websockets

app = FastAPI()

# Configurar rutas y dependencias...

# Integrar WebSockets
integrate_websockets(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
