"""
Script para probar la funcionalidad de obtener todos los usuarios vía WebSocket.
"""

import asyncio
import websockets
import json
import logging
import sys
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# URL del servidor WebSocket (local o remoto)
WS_URL = "ws://localhost:8000/ws"  # Cambiar según corresponda

async def test_get_all_users():
    """Prueba la funcionalidad de obtener todos los usuarios."""
    try:
        logger.info(f"Conectando a {WS_URL}...")
        async with websockets.connect(WS_URL) as websocket:
            logger.info("Conexión establecida")
            
            # Esperar mensaje de conexión
            response = await websocket.recv()
            logger.info(f"Mensaje de conexión recibido: {response}")
            
            # Crear solicitud para obtener todos los usuarios
            request = {
                "type": "request",
                "id": "test-request-1",
                "resource": "users",
                "payload": {
                    "action": "get_all"
                }
            }
            
            # Enviar solicitud
            logger.info(f"Enviando solicitud: {json.dumps(request)}")
            await websocket.send(json.dumps(request))
            
            # Recibir respuesta
            response = await websocket.recv()
            response_data = json.loads(response)
            
            # Mostrar respuesta
            logger.info(f"Respuesta recibida: {json.dumps(response_data, indent=2)}")
            
            # Verificar si se obtuvieron usuarios
            if response_data.get("type") == "response":
                users = response_data.get("payload", {}).get("users", [])
                total = response_data.get("payload", {}).get("total", 0)
                logger.info(f"Se obtuvieron {total} usuarios")
                
                # Mostrar información de usuarios
                for i, user in enumerate(users):
                    logger.info(f"Usuario {i+1}: {user.get('full_name')} - {user.get('email')} - {user.get('phone')}")
            else:
                logger.error(f"Error en la respuesta: {response_data}")
    
    except Exception as e:
        logger.error(f"Error durante la prueba: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def run_test():
    """Ejecuta la prueba."""
    asyncio.run(test_get_all_users())

if __name__ == "__main__":
    run_test()
