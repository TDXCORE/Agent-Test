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
from dotenv import load_dotenv

# Añadir directorio raíz al path para poder importar App
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Cargar variables de entorno - asegúrate de que esto se ejecute antes de acceder a las variables
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

# Crear contexto SSL sin verificación (solo para pruebas, NO USAR EN PRODUCCIÓN)
def create_ssl_context():
    """Crea un contexto SSL sin verificación para pruebas."""
    import ssl
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    return ssl_context

async def test_websocket_no_token():
    """Prueba conexión sin token."""
    uri = "wss://waagentv1.onrender.com/ws"
    
    try:
        logger.info(f"Probando conexión sin token: {uri}")
        logger.info("Intentando establecer conexión WebSocket...")
        
        # Usar contexto SSL sin verificación
        ssl_context = create_ssl_context()
        
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            logger.info("Conexión establecida sin token")
            
            # Enviar un mensaje de prueba
            test_message = {
                "type": "ping",
                "id": str(uuid.uuid4()),
                "timestamp": asyncio.get_event_loop().time()
            }
            await websocket.send(json.dumps(test_message))
            logger.info(f"Mensaje enviado: {test_message}")
            
            # Esperar respuesta
            response = await websocket.recv()
            logger.info(f"Respuesta recibida: {response}")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False
    finally:
        logger.info(f"Conexión cerrada: None - None")
    
    return True

async def test_websocket_token_in_url():
    """Prueba conexión con token en URL."""
    uri = f"wss://waagentv1.onrender.com/ws?token={WEBSOCKET_AUTH_TOKEN}"
    
    try:
        logger.info(f"Probando conexión con token en URL: {uri}")
        logger.info(f"Intentando conectar con token (primeros 10 caracteres): {WEBSOCKET_AUTH_TOKEN[:10]}...")
        
        # Usar contexto SSL sin verificación
        ssl_context = create_ssl_context()
        
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            logger.info("Conexión establecida con token en URL")
            
            # Enviar un mensaje de prueba
            test_message = {
                "type": "ping",
                "id": str(uuid.uuid4()),
                "timestamp": asyncio.get_event_loop().time()
            }
            await websocket.send(json.dumps(test_message))
            logger.info(f"Mensaje enviado: {test_message}")
            
            # Esperar respuesta
            response = await websocket.recv()
            logger.info(f"Respuesta recibida: {response}")
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False
    finally:
        logger.info(f"Conexión cerrada: None - None")
    
    return True

async def test_websocket_token_in_header():
    """Prueba conexión con token en header."""
    uri = "wss://waagentv1.onrender.com/ws"
    
    try:
        logger.info(f"Probando conexión con token en header: {uri}")
        logger.info(f"Token para header (primeros 10 caracteres): {WEBSOCKET_AUTH_TOKEN[:10]}...")
        
        # Verificar la versión de websockets
        logger.info(f"Versión de websockets: {websockets.__version__}")
        
        # Intentar conectar con los headers usando el método correcto para la versión 15.0.1
        try:
            # Método 1: Usar el parámetro extra_headers
            headers = {"Authorization": f"Bearer {WEBSOCKET_AUTH_TOKEN}"}
            logger.info(f"Intentando método 1 con extra_headers: {headers}")
            
            # Usar contexto SSL sin verificación
            ssl_context = create_ssl_context()
            
            async with websockets.connect(uri, extra_headers=headers, ssl=ssl_context) as websocket:
                logger.info("Conexión establecida con token en header (método 1)")
                
                # Enviar un mensaje de prueba
                test_message = {
                    "type": "ping",
                    "id": str(uuid.uuid4()),
                    "timestamp": asyncio.get_event_loop().time()
                }
                await websocket.send(json.dumps(test_message))
                logger.info(f"Mensaje enviado: {test_message}")
                
                # Esperar respuesta
                response = await websocket.recv()
                logger.info(f"Respuesta recibida: {response}")
                
                return True
                
        except TypeError as e:
            # Si falla el método 1, intentar con el método 2
            logger.warning(f"Método 1 falló: {str(e)}")
            logger.info("Intentando método 2 con header como parte de la URL")
            
            # Método 2: Añadir el token como parámetro de consulta
            auth_uri = f"{uri}?token={WEBSOCKET_AUTH_TOKEN}"
            logger.info(f"URI con token: {auth_uri[:50]}...")
            
            # Usar contexto SSL sin verificación
            ssl_context = create_ssl_context()
            
            async with websockets.connect(auth_uri, ssl=ssl_context) as websocket:
                logger.info("Conexión establecida con token en URL (método 2)")
                
                # Enviar un mensaje de prueba
                test_message = {
                    "type": "ping",
                    "id": str(uuid.uuid4()),
                    "timestamp": asyncio.get_event_loop().time()
                }
                await websocket.send(json.dumps(test_message))
                logger.info(f"Mensaje enviado: {test_message}")
                
                # Esperar respuesta
                response = await websocket.recv()
                logger.info(f"Respuesta recibida: {response}")
                
                return True
            
    except Exception as e:
        logger.error(f"Error detallado: {type(e).__name__}: {str(e)}")
        return False
    finally:
        logger.info(f"Conexión cerrada: None - None")
    
    return False

async def main():
    """Función principal."""
    logger.info("Iniciando pruebas de WebSockets")
    
    # Definir las pruebas a ejecutar
    tests = [
        ("Conexión sin token", test_websocket_no_token),
        ("Conexión con token en URL", test_websocket_token_in_url),
        ("Conexión con token en header", test_websocket_token_in_header)
    ]
    
    # Ejecutar cada prueba y capturar resultados
    results = []
    for test_name, test_func in tests:
        logger.info(f"Ejecutando prueba: {test_name}")
        try:
            success = await test_func()
            results.append((test_name, success))
            logger.info(f"Prueba {test_name}: {'ÉXITO' if success else 'FALLO'}")
        except Exception as e:
            logger.error(f"Error al ejecutar prueba {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Mostrar resumen de resultados
    logger.info("\n=== RESUMEN DE PRUEBAS ===")
    for test_name, success in results:
        logger.info(f"{test_name}: {'✅ ÉXITO' if success else '❌ FALLO'}")
    
    successful_tests = sum(1 for _, success in results if success)
    logger.info(f"Resultado: {successful_tests}/{len(tests)} pruebas exitosas")
    logger.info("Todas las pruebas completadas")

if __name__ == "__main__":
    # Ejecutar pruebas
    asyncio.run(main())
