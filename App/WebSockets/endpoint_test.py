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
        
        # Intentar conectar con más detalles de error
        try:
            # Aumentar el timeout para dar más tiempo a la conexión
            websocket = await asyncio.wait_for(
                websockets.connect(url, ssl=ssl_context),
                timeout=15.0
            )
            
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
                await websocket.close()
                return True, "Conexión exitosa con respuesta"
            except asyncio.TimeoutError:
                logger.warning("Timeout esperando respuesta")
                await websocket.close()
                return True, "Conexión establecida pero sin respuesta"
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout al intentar conectar a {url}")
            return False, "Timeout al conectar"
            
    except websockets.exceptions.InvalidStatusCode as e:
        error_msg = f"InvalidStatus: {str(e)}"
        logger.error(f"Error: {error_msg}")
        return False, error_msg
    
    except websockets.exceptions.InvalidURI as e:
        error_msg = f"InvalidURI: {str(e)}"
        logger.error(f"Error: {error_msg}")
        return False, error_msg
    
    except websockets.exceptions.ConnectionClosed as e:
        error_msg = f"ConnectionClosed: {str(e)}"
        logger.error(f"Error: {error_msg}")
        return False, error_msg
    
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
    
    # Primero probar el endpoint principal con más detalle
    logger.info("\n=== PRUEBA DETALLADA DEL ENDPOINT PRINCIPAL ===")
    success, message = await test_endpoint(base_url, "/ws", with_token=True)
    if success:
        logger.info(f"✅ ÉXITO - Endpoint principal /ws funciona correctamente")
        logger.info(f"Detalles: {message}")
    else:
        logger.error(f"❌ FALLO - Endpoint principal /ws no funciona")
        logger.error(f"Detalles: {message}")
    
    # Probar también sin token para ver si es un problema de autenticación
    success_no_token, message_no_token = await test_endpoint(base_url, "/ws", with_token=False)
    if success_no_token:
        logger.info(f"✅ ÉXITO - Endpoint principal /ws funciona sin token")
        logger.info(f"Detalles: {message_no_token}")
    else:
        logger.error(f"❌ FALLO - Endpoint principal /ws no funciona sin token")
        logger.error(f"Detalles: {message_no_token}")
    
    # Ahora probar todos los endpoints
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
    
    # Recomendaciones basadas en resultados
    logger.info("\n=== RECOMENDACIONES ===")
    
    if successful_tests == 0:
        logger.info("- Verifica que el servidor WebSocket esté en ejecución")
        logger.info("- Comprueba la configuración CORS en el servidor")
        logger.info("- Verifica que el token de autenticación sea válido")
        logger.info("- Prueba con una conexión local para descartar problemas de red")
    elif successful_tests < len(results) / 2:
        logger.info("- Algunos endpoints funcionan, pero otros no")
        logger.info("- Verifica la configuración de rutas en el servidor")
        logger.info("- Asegúrate de que todos los endpoints estén correctamente configurados")
    else:
        logger.info("- La mayoría de los endpoints funcionan correctamente")
        logger.info("- Considera estandarizar en un único endpoint (/ws)")
    
    logger.info("Todas las pruebas completadas")

if __name__ == "__main__":
    asyncio.run(main())
