"""
Script simple para probar la funcionalidad básica de WebSockets.
Este script no requiere pytest y puede ejecutarse directamente.
"""

import asyncio
import json
import logging
import sys
import os
import uuid
import websockets

# Añadir directorio raíz al path para poder importar App
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_websocket_connection():
    """Prueba simple de conexión WebSocket."""
    uri = "ws://localhost:8000/ws"
    
    try:
        logger.info(f"Conectando a {uri}...")
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
            
            # Verificar que la respuesta corresponde a nuestra solicitud
            if response_data.get("id") == request_id:
                logger.info("Prueba exitosa: ID de respuesta coincide con ID de solicitud")
            else:
                logger.error("Prueba fallida: ID de respuesta no coincide con ID de solicitud")
            
            logger.info("Cerrando conexión")
    
    except Exception as e:
        logger.error(f"Error durante la prueba: {str(e)}")
        return False
    
    return True

async def main():
    """Función principal."""
    logger.info("Iniciando prueba simple de WebSockets")
    
    success = await test_websocket_connection()
    
    if success:
        logger.info("Prueba completada exitosamente")
    else:
        logger.error("Prueba fallida")

if __name__ == "__main__":
    # Ejecutar prueba
    asyncio.run(main())
