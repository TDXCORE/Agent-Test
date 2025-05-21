"""
Script para probar el servidor WebSocket local.
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

async def test_websocket():
    """Prueba la conexión al servidor WebSocket local."""
    # URL del servidor WebSocket local
    url = f"ws://localhost:8766/ws?token={WEBSOCKET_AUTH_TOKEN}"
    
    logger.info(f"Conectando a {url}...")
    
    try:
        # Conectar al WebSocket
        async with websockets.connect(url) as websocket:
            logger.info("Conexión establecida")
            
            # Esperar mensaje de bienvenida
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            logger.info(f"Mensaje de bienvenida recibido: {welcome_data}")
            
            # Enviar solicitud de conversaciones
            request = {
                "type": "request",
                "id": "test-123",
                "resource": "conversations",
                "payload": {
                    "action": "get_all",
                    "user_id": "test_user"
                }
            }
            logger.info(f"Enviando solicitud: {request}")
            await websocket.send(json.dumps(request))
            
            # Esperar respuesta
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Respuesta recibida: {response_data}")
            
            # Esperar evento
            event = await websocket.recv()
            event_data = json.loads(event)
            logger.info(f"Evento recibido: {event_data}")
            
            # Enviar solicitud de mensajes
            request = {
                "type": "request",
                "id": "test-456",
                "resource": "messages",
                "payload": {
                    "action": "get_by_conversation",
                    "conversation_id": "conv-1"
                }
            }
            logger.info(f"Enviando solicitud: {request}")
            await websocket.send(json.dumps(request))
            
            # Esperar respuesta
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Respuesta recibida: {response_data}")
            
            # Esperar evento
            event = await websocket.recv()
            event_data = json.loads(event)
            logger.info(f"Evento recibido: {event_data}")
            
            # Enviar solicitud de usuarios
            request = {
                "type": "request",
                "id": "test-789",
                "resource": "users",
                "payload": {
                    "action": "get_all"
                }
            }
            logger.info(f"Enviando solicitud: {request}")
            await websocket.send(json.dumps(request))
            
            # Esperar respuesta
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Respuesta recibida: {response_data}")
            
            # Esperar evento
            event = await websocket.recv()
            event_data = json.loads(event)
            logger.info(f"Evento recibido: {event_data}")
            
            logger.info("Pruebas completadas exitosamente")
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")

async def main():
    """Función principal."""
    await test_websocket()

if __name__ == "__main__":
    asyncio.run(main())
