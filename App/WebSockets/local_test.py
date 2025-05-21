"""
Script para probar la conexión WebSocket localmente.
"""

import asyncio
import json
import logging
import sys
import os
import uuid
import websockets
from dotenv import load_dotenv

# Añadir directorio raíz al path para poder importar App
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Obtener el token de autenticación de variable de entorno
WEBSOCKET_AUTH_TOKEN = os.getenv("WEBSOCKET_AUTH_TOKEN", "")
if not WEBSOCKET_AUTH_TOKEN:
    logger.warning("WEBSOCKET_AUTH_TOKEN no está definido en las variables de entorno")
else:
    # Mostrar los primeros caracteres del token para depuración
    logger.info(f"Token cargado (primeros 10 caracteres): {WEBSOCKET_AUTH_TOKEN[:10]}...")

async def test_websocket_local():
    """Prueba conexión WebSocket local."""
    uri = "ws://localhost:8000/ws"
    
    if WEBSOCKET_AUTH_TOKEN:
        uri += f"?token={WEBSOCKET_AUTH_TOKEN}"
    
    try:
        logger.info(f"Conectando a {uri}")
        
        async with websockets.connect(uri) as websocket:
            logger.info("Conexión establecida")
            
            # Esperar mensaje de bienvenida
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            logger.info(f"Mensaje de bienvenida recibido: {welcome_data}")
            
            # Enviar solicitud para obtener conversaciones
            request_id = str(uuid.uuid4())
            request = {
                "type": "request",
                "id": request_id,
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
            
            # Enviar solicitud para crear un mensaje
            request_id = str(uuid.uuid4())
            request = {
                "type": "request",
                "id": request_id,
                "resource": "messages",
                "payload": {
                    "action": "create",
                    "message": {
                        "conversation_id": "test_conversation",
                        "content": "Mensaje de prueba desde WebSocket",
                        "role": "user"
                    }
                }
            }
            
            logger.info(f"Enviando solicitud para crear mensaje: {request}")
            await websocket.send(json.dumps(request))
            
            # Esperar respuesta
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Respuesta recibida: {response_data}")
            
            # Mantener la conexión abierta por un tiempo para recibir eventos
            logger.info("Esperando eventos por 5 segundos...")
            try:
                for _ in range(5):
                    try:
                        # Esperar mensaje con timeout de 1 segundo
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        message_data = json.loads(message)
                        logger.info(f"Evento recibido: {message_data}")
                    except asyncio.TimeoutError:
                        # Timeout esperado, continuar
                        pass
            except Exception as e:
                logger.error(f"Error al esperar eventos: {str(e)}")
            
            logger.info("Prueba completada con éxito")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False
    
    return True

async def main():
    """Función principal."""
    logger.info("Iniciando prueba de WebSocket local")
    
    success = await test_websocket_local()
    
    if success:
        logger.info("✅ Prueba exitosa")
    else:
        logger.error("❌ Prueba fallida")

if __name__ == "__main__":
    asyncio.run(main())
