"""
Script para probar la conexión a un servidor WebSocket público (echo.websocket.org).
Este script ayuda a verificar si la biblioteca websockets está funcionando correctamente.
"""

import asyncio
import logging
import websockets
import json
import uuid
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

async def test_echo_websocket():
    """Prueba conexión a ws.postman-echo.com."""
    uri = "wss://ws.postman-echo.com/raw"
    
    try:
        logger.info(f"Conectando a {uri}...")
        
        # Deshabilitar verificación SSL para pruebas (NO USAR EN PRODUCCIÓN)
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            logger.info("Conexión establecida con ws.postman-echo.com")
            
            # Enviar un mensaje de prueba
            test_message = {
                "type": "echo",
                "id": str(uuid.uuid4()),
                "message": "Hola, WebSocket!"
            }
            message_str = json.dumps(test_message)
            
            logger.info(f"Enviando mensaje: {message_str}")
            await websocket.send(message_str)
            
            # Recibir respuesta
            response = await websocket.recv()
            logger.info(f"Respuesta recibida: {response}")
            
            # Verificar que la respuesta es igual al mensaje enviado
            if response == message_str:
                logger.info("✅ Prueba exitosa: El servidor echo devolvió el mismo mensaje")
                return True
            else:
                logger.error("❌ Prueba fallida: El servidor echo devolvió un mensaje diferente")
                return False
            
    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {str(e)}")
        return False
    finally:
        logger.info("Conexión cerrada")

async def main():
    """Función principal."""
    logger.info("Iniciando prueba de conexión a ws.postman-echo.com")
    
    success = await test_echo_websocket()
    
    if success:
        logger.info("La biblioteca websockets está funcionando correctamente")
        logger.info("El problema probablemente está en la configuración del servidor o en el token")
    else:
        logger.info("Hay un problema con la biblioteca websockets o con la conexión a Internet")
    
    logger.info("Prueba completada")

if __name__ == "__main__":
    asyncio.run(main())
