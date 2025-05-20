"""
Configuración de WebSockets para la aplicación.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query, Header
from typing import Dict, Any, Optional, List, Callable
import logging
import json
import uuid
import asyncio
from datetime import datetime, timedelta

from .connection import ConnectionManager
from .auth import verify_token
from .handlers import ConversationsHandler, MessagesHandler, UsersHandler
from .events.listeners import setup_listeners

logger = logging.getLogger(__name__)

# Instancia global del gestor de conexiones
connection_manager = ConnectionManager()

# Handlers para diferentes tipos de recursos
handlers = {}

async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None)
):
    """Endpoint principal para conexiones WebSocket."""
    client_id = str(uuid.uuid4())
    user_id = None
    
    # Extraer token de Authorization si no se proporcionó como query param
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    
    # Verificar autenticación si se proporcionó token
    if token:
        is_valid, user_data = await verify_token(token)
        if is_valid and user_data:
            user_id = user_data.get("user_id")
            logger.info(f"Usuario autenticado: {user_id}")
        else:
            # Rechazar conexión si el token es inválido
            await websocket.close(code=1008)  # Policy Violation
            logger.warning(f"Intento de conexión con token inválido")
            return
    
    # Aceptar conexión
    try:
        await connection_manager.connect(websocket, client_id, user_id)
        
        # Enviar mensaje de bienvenida
        await connection_manager.send_json(websocket, {
            "type": "connected",
            "id": str(uuid.uuid4()),
            "payload": {
                "client_id": client_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        })
        
        # Bucle principal para recibir mensajes
        while True:
            try:
                # Recibir mensaje
                message_text = await websocket.receive_text()
                message = json.loads(message_text)
                
                # Procesar mensaje según su tipo
                resource_type = message.get("resource")
                
                if not resource_type:
                    await connection_manager.send_json(websocket, {
                        "type": "error",
                        "id": message.get("id", str(uuid.uuid4())),
                        "payload": {
                            "code": "missing_resource",
                            "message": "El mensaje debe especificar un recurso"
                        }
                    })
                    continue
                
                # Obtener handler para el tipo de recurso
                handler = handlers.get(resource_type)
                
                if not handler:
                    await connection_manager.send_json(websocket, {
                        "type": "error",
                        "id": message.get("id", str(uuid.uuid4())),
                        "payload": {
                            "code": "unknown_resource",
                            "message": f"Recurso desconocido: {resource_type}"
                        }
                    })
                    continue
                
                # Procesar mensaje con el handler correspondiente
                await handler.handle_message(websocket, message)
            
            except WebSocketDisconnect:
                logger.info(f"Cliente {client_id} desconectado")
                break
            
            except json.JSONDecodeError:
                logger.warning(f"Mensaje JSON inválido recibido de {client_id}")
                await connection_manager.send_json(websocket, {
                    "type": "error",
                    "id": str(uuid.uuid4()),
                    "payload": {
                        "code": "invalid_json",
                        "message": "El mensaje debe ser un JSON válido"
                    }
                })
            
            except Exception as e:
                logger.error(f"Error al procesar mensaje de {client_id}: {str(e)}")
                await connection_manager.send_json(websocket, {
                    "type": "error",
                    "id": str(uuid.uuid4()),
                    "payload": {
                        "code": "internal_error",
                        "message": "Error interno del servidor"
                    }
                })
    
    except Exception as e:
        logger.error(f"Error en websocket_endpoint: {str(e)}")
    
    finally:
        # Asegurar que la conexión se cierre correctamente
        connection_manager.disconnect(websocket)

async def heartbeat_task():
    """Tarea periódica para enviar heartbeats y limpiar conexiones inactivas."""
    while True:
        try:
            # Esperar 30 segundos
            await asyncio.sleep(30)
            
            # Enviar heartbeat a todas las conexiones activas
            for websocket in list(connection_manager.active_connections):
                try:
                    await connection_manager.send_json(websocket, {
                        "type": "heartbeat",
                        "id": str(uuid.uuid4()),
                        "payload": {
                            "timestamp": datetime.now().isoformat()
                        }
                    })
                except Exception:
                    # Si falla, desconectar
                    connection_manager.disconnect(websocket)
            
            # Limpiar conexiones inactivas (sin actividad por más de 5 minutos)
            timeout = datetime.now() - timedelta(minutes=5)
            for websocket in list(connection_manager.active_connections):
                last_activity = connection_manager.last_activity.get(websocket)
                if last_activity and last_activity < timeout:
                    logger.info(f"Desconectando cliente inactivo")
                    connection_manager.disconnect(websocket)
        
        except Exception as e:
            logger.error(f"Error en heartbeat_task: {str(e)}")

def setup_websockets(app: FastAPI):
    """Configura los WebSockets en la aplicación."""
    global handlers
    
    # Inicializar handlers
    handlers = {
        "conversations": ConversationsHandler(connection_manager),
        "messages": MessagesHandler(connection_manager),
        "users": UsersHandler(connection_manager)
    }
    
    # Configurar listeners de eventos
    setup_listeners(connection_manager)
    
    # Registrar endpoint WebSocket
    app.websocket("/ws")(websocket_endpoint)
    
    # Iniciar tarea de heartbeat
    @app.on_event("startup")
    async def start_heartbeat():
        asyncio.create_task(heartbeat_task())
    
    logger.info("WebSockets configurados correctamente")
