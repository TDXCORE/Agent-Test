"""
Script para probar la conexión WebSocket específicamente con el despliegue en Render.
Este script se enfoca en el endpoint /ws que parece ser el único que funciona según los logs.
"""

import asyncio
import logging
import websockets
import json
import uuid
import ssl
from dotenv import load_dotenv
import os
import sys

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

async def test_render_websocket(with_token=True):
    """
    Prueba la conexión WebSocket con el despliegue en Render.
    
    Args:
        with_token: Si se debe incluir el token de autenticación
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje)
    """
    # URL del servidor en Render
    base_url = "wss://waagentv1.onrender.com"
    endpoint = "/ws"
    url = f"{base_url}{endpoint}"
    
    # Añadir token si se solicita
    if with_token and WEBSOCKET_AUTH_TOKEN:
        url = f"{url}?token={WEBSOCKET_AUTH_TOKEN}"
    
    logger.info(f"Probando conexión a: {url}")
    
    try:
        # Usar contexto SSL sin verificación
        ssl_context = create_ssl_context()
        
        # Intentar conectar con timeout extendido
        try:
            websocket = await asyncio.wait_for(
                websockets.connect(url, ssl=ssl_context, ping_interval=20, ping_timeout=20),
                timeout=20.0
            )
            
            logger.info(f"✅ Conexión establecida con {url}")
            
            # Esperar mensaje de bienvenida
            try:
                welcome = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome)
                logger.info(f"Mensaje de bienvenida recibido: {welcome_data}")
                
                # Extraer client_id si está disponible
                client_id = None
                if "payload" in welcome_data and "client_id" in welcome_data["payload"]:
                    client_id = welcome_data["payload"]["client_id"]
                    logger.info(f"ID de cliente asignado: {client_id}")
                
                # Enviar un mensaje de prueba
                test_message = {
                    "type": "ping",
                    "id": str(uuid.uuid4()),
                    "message": "Prueba de conexión desde render_test.py"
                }
                message_str = json.dumps(test_message)
                
                logger.info(f"Enviando mensaje: {message_str}")
                await websocket.send(message_str)
                
                # Esperar respuesta
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    logger.info(f"Respuesta recibida: {response}")
                    
                    # Probar una solicitud real
                    request = {
                        "type": "request",
                        "id": str(uuid.uuid4()),
                        "resource": "conversations",
                        "payload": {
                            "action": "get_all",
                            "user_id": "test_user_" + str(uuid.uuid4())[:8]
                        }
                    }
                    
                    logger.info(f"Enviando solicitud: {json.dumps(request)}")
                    await websocket.send(json.dumps(request))
                    
                    # Esperar respuesta a la solicitud
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    logger.info(f"Respuesta a solicitud recibida: {response}")
                    
                    # Escuchar eventos durante unos segundos
                    logger.info("Escuchando eventos durante 5 segundos...")
                    start_time = asyncio.get_event_loop().time()
                    events = []
                    
                    while asyncio.get_event_loop().time() - start_time < 5:
                        try:
                            event = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                            logger.info(f"Evento recibido: {event}")
                            events.append(event)
                        except asyncio.TimeoutError:
                            # Timeout esperado, continuar escuchando
                            pass
                    
                    logger.info(f"Total de eventos recibidos: {len(events)}")
                    
                    # Cerrar conexión
                    await websocket.close()
                    logger.info("Conexión cerrada correctamente")
                    
                    return True, "Prueba completa exitosa"
                    
                except asyncio.TimeoutError:
                    logger.warning("Timeout esperando respuesta al mensaje")
                    await websocket.close()
                    return True, "Conexión establecida pero sin respuesta al mensaje"
                
            except asyncio.TimeoutError:
                logger.warning("Timeout esperando mensaje de bienvenida")
                await websocket.close()
                return True, "Conexión establecida pero sin mensaje de bienvenida"
            
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

async def main():
    """Función principal."""
    logger.info("=== PRUEBA DE WEBSOCKET EN RENDER ===")
    
    # Probar con token
    logger.info("\n--- Prueba con token ---")
    success_with_token, message_with_token = await test_render_websocket(with_token=True)
    
    # Probar sin token
    logger.info("\n--- Prueba sin token ---")
    success_without_token, message_without_token = await test_render_websocket(with_token=False)
    
    # Mostrar resumen
    logger.info("\n=== RESUMEN DE PRUEBAS ===")
    
    if success_with_token:
        logger.info("✅ Conexión con token: EXITOSA")
        logger.info(f"Detalles: {message_with_token}")
    else:
        logger.error("❌ Conexión con token: FALLIDA")
        logger.error(f"Detalles: {message_with_token}")
    
    if success_without_token:
        logger.info("✅ Conexión sin token: EXITOSA")
        logger.info(f"Detalles: {message_without_token}")
    else:
        logger.error("❌ Conexión sin token: FALLIDA")
        logger.error(f"Detalles: {message_without_token}")
    
    # Recomendaciones
    logger.info("\n=== RECOMENDACIONES ===")
    
    if success_with_token and success_without_token:
        logger.info("- El servidor WebSocket está funcionando correctamente")
        logger.info("- La autenticación parece ser opcional (funciona con y sin token)")
    elif success_with_token:
        logger.info("- El servidor WebSocket está funcionando correctamente")
        logger.info("- La autenticación es requerida (solo funciona con token)")
    elif success_without_token:
        logger.info("- El servidor WebSocket está funcionando correctamente")
        logger.info("- La autenticación está fallando (funciona sin token pero no con token)")
        logger.info("- Verifica que el token sea válido")
    else:
        logger.info("- El servidor WebSocket no está funcionando correctamente")
        logger.info("- Verifica que el servidor esté en ejecución")
        logger.info("- Comprueba la configuración de CORS")
        logger.info("- Verifica que el endpoint /ws esté correctamente configurado")
    
    # Resultado final
    if success_with_token or success_without_token:
        logger.info("\n✅ RESULTADO FINAL: Al menos una prueba fue exitosa")
        return 0
    else:
        logger.error("\n❌ RESULTADO FINAL: Todas las pruebas fallaron")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
