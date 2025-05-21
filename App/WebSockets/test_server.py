"""
Script para ejecutar un servidor WebSocket local de prueba.
"""

import asyncio
import websockets
import json
import logging
import os
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Obtener token de WebSocket
WEBSOCKET_AUTH_TOKEN = os.getenv("WEBSOCKET_AUTH_TOKEN", "ws_auth_token_2025_secure_connection")

# Diccionario para almacenar conexiones activas
active_connections = {}

async def handle_connection(websocket):
    """Maneja una conexión WebSocket."""
    # Extraer token de la URL si existe
    path = websocket.path
    token = None
    if "?" in path:
        query_string = path.split("?")[1]
        params = query_string.split("&")
        for param in params:
            if param.startswith("token="):
                token = param.split("=")[1]
                break
    
    # Verificar token
    if not token or token != WEBSOCKET_AUTH_TOKEN:
        logger.warning(f"Intento de conexión con token inválido: {token}")
        await websocket.close(1008, "Token inválido")
        return
    
    # Generar ID de cliente
    client_id = f"client-{len(active_connections) + 1}"
    active_connections[client_id] = websocket
    
    logger.info(f"Nueva conexión: {client_id}")
    
    try:
        # Enviar mensaje de bienvenida
        welcome_message = {
            "type": "welcome",
            "payload": {
                "client_id": client_id,
                "message": "Bienvenido al servidor WebSocket de prueba"
            }
        }
        await websocket.send(json.dumps(welcome_message))
        
        # Procesar mensajes
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Mensaje recibido de {client_id}: {data}")
                
                # Procesar solicitud
                if data.get("type") == "request":
                    resource = data.get("resource")
                    action = data.get("payload", {}).get("action")
                    
                    # Responder con un eco de la solicitud
                    response = {
                        "type": "response",
                        "id": data.get("id"),
                        "resource": resource,
                        "payload": {
                            "success": True,
                            "message": f"Solicitud procesada: {resource}.{action}",
                            "data": data.get("payload")
                        }
                    }
                    
                    # Si es una solicitud de conversaciones, añadir datos de ejemplo
                    if resource == "conversations" and action == "get_all":
                        response["payload"]["conversations"] = [
                            {"id": "conv-1", "title": "Conversación de prueba 1"},
                            {"id": "conv-2", "title": "Conversación de prueba 2"}
                        ]
                    
                    # Si es una solicitud de mensajes, añadir datos de ejemplo
                    elif resource == "messages" and action == "get_by_conversation":
                        response["payload"]["messages"] = [
                            {"id": "msg-1", "content": "Mensaje de prueba 1"},
                            {"id": "msg-2", "content": "Mensaje de prueba 2"}
                        ]
                    
                    # Si es una solicitud de usuarios, añadir datos de ejemplo
                    elif resource == "users" and action == "get_all":
                        response["payload"]["users"] = [
                            {"id": "user-1", "name": "Usuario de prueba 1"},
                            {"id": "user-2", "name": "Usuario de prueba 2"}
                        ]
                    
                    await websocket.send(json.dumps(response))
                    
                    # Enviar un evento de ejemplo después de cada solicitud
                    event = {
                        "type": "event",
                        "resource": resource,
                        "payload": {
                            "event_type": f"{resource}.updated",
                            "data": {"timestamp": "2025-05-20T23:59:59Z"}
                        }
                    }
                    await websocket.send(json.dumps(event))
                
            except json.JSONDecodeError:
                logger.warning(f"Mensaje no JSON recibido de {client_id}: {message}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "payload": {
                        "message": "Formato de mensaje inválido, se esperaba JSON"
                    }
                }))
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Conexión cerrada: {client_id}")
    
    finally:
        # Eliminar conexión del diccionario
        if client_id in active_connections:
            del active_connections[client_id]

async def main():
    """Función principal."""
    # Iniciar servidor WebSocket
    host = "localhost"
    port = 8766
    
    logger.info(f"Iniciando servidor WebSocket en {host}:{port}")
    logger.info(f"Token de autenticación: {WEBSOCKET_AUTH_TOKEN}")
    
    async with websockets.serve(handle_connection, host, port):
        logger.info(f"Servidor WebSocket iniciado en ws://{host}:{port}")
        await asyncio.Future()  # Ejecutar indefinidamente

if __name__ == "__main__":
    asyncio.run(main())
