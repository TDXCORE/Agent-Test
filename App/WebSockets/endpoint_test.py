"""
Script para probar diferentes endpoints WebSocket en el servidor.
"""

import asyncio
import logging
import websockets
import json
import uuid
import ssl
from dotenv import load_dotenv
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Obtener token de autenticación
WEBSOCKET_AUTH_TOKEN = os.getenv("WEBSOCKET_AUTH_TOKEN", "")
if not WEBSOCKET_AUTH_TOKEN:
    logger.warning("WEBSOCKET_AUTH_TOKEN no está definido en las variables de entorno")
else:
    logger.info(f"Token cargado (primeros 10 caracteres): {WEBSOCKET_AUTH_TOKEN[:10]}...")

# Crear contexto SSL sin verificación (solo para pruebas)
def create_ssl_context():
    """Crea un contexto SSL sin verificación para pruebas."""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context

async def test_endpoint(base_url, endpoint, with_token=True):
    """Prueba un endpoint WebSocket específico."""
    # Construir URL completa
    url = f"{base_url}{endpoint}"
    
    # Añadir token si se solicita
    if with_token:
        url = f"{url}?token={WEBSOCKET_AUTH_TOKEN}"
    
    try:
        logger.info(f"Probando conexión a: {url}")
        
        # Usar contexto SSL sin verificación
        ssl_context = create_ssl_context()
        
        # Intentar conectar
        async with websockets.connect(url, ssl=ssl_context) as websocket:
            logger.info(f"✅ Conexión establecida con {url}")
            
            # Enviar un mensaje de prueba
            test_message = {
                "type": "ping",
                "id": str(uuid.uuid4()),
                "message": "Prueba de conexión"
            }
            message_str = json.dumps(test_message)
            
            logger.info(f"Enviando mensaje: {message_str}")
            await websocket.send(message_str)
            
            # Esperar respuesta con timeout
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                logger.info(f"Respuesta recibida: {response}")
                return True, "Conexión exitosa"
            except asyncio.TimeoutError:
                logger.warning("Timeout esperando respuesta")
                return True, "Conexión establecida pero sin respuesta"
            
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Error: {error_msg}")
        return False, error_msg
    finally:
        logger.info(f"Prueba de {url} completada")

async def main():
    """Función principal."""
    logger.info("Iniciando pruebas de diferentes endpoints WebSocket")
    
    # Base URL del servidor
    base_url = "wss://waagentv1.onrender.com"
    
    # Lista de endpoints a probar
    endpoints = [
        "/ws",              # Endpoint estándar
        "/websocket",       # Alternativa común
        "/socket",          # Otra alternativa
        "/",                # Raíz
        "/api/ws",          # Bajo /api
        "/api/websocket",   # Otra ubicación común
        "/v1/ws",           # Con versión
        "/chat/ws",         # Específico para chat
    ]
    
    # Probar cada endpoint con y sin token
    results = []
    
    for endpoint in endpoints:
        # Probar con token
        success, message = await test_endpoint(base_url, endpoint, with_token=True)
        results.append((f"{endpoint} (con token)", success, message))
        
        # Probar sin token
        success, message = await test_endpoint(base_url, endpoint, with_token=False)
        results.append((f"{endpoint} (sin token)", success, message))
    
    # Mostrar resumen de resultados
    logger.info("\n=== RESUMEN DE PRUEBAS ===")
    
    for endpoint, success, message in results:
        status = "✅ ÉXITO" if success else "❌ FALLO"
        logger.info(f"{endpoint}: {status} - {message}")
    
    # Contar éxitos
    successful_tests = sum(1 for _, success, _ in results if success)
    logger.info(f"Resultado: {successful_tests}/{len(results)} pruebas exitosas")
    
    logger.info("Todas las pruebas completadas")

if __name__ == "__main__":
    asyncio.run(main())
