"""
Script para probar la conexión HTTP básica al servidor.
"""

import requests
import logging
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

def test_http_endpoint(url, with_token=False):
    """Prueba un endpoint HTTP."""
    headers = {}
    params = {}
    
    if with_token:
        # Probar con token en header
        headers["Authorization"] = f"Bearer {WEBSOCKET_AUTH_TOKEN}"
        # También probar con token en query param
        params["token"] = WEBSOCKET_AUTH_TOKEN
    
    try:
        logger.info(f"Probando conexión HTTP a: {url}")
        logger.info(f"Headers: {headers}")
        logger.info(f"Params: {params}")
        
        response = requests.get(url, headers=headers, params=params, verify=False, timeout=10)
        
        logger.info(f"Respuesta: {response.status_code} {response.reason}")
        logger.info(f"Headers de respuesta: {dict(response.headers)}")
        
        # Intentar mostrar el cuerpo de la respuesta
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                logger.info(f"Cuerpo JSON: {response.json()}")
            else:
                # Mostrar solo los primeros 500 caracteres para evitar respuestas muy largas
                body = response.text[:500]
                if len(response.text) > 500:
                    body += "... [truncado]"
                logger.info(f"Cuerpo: {body}")
        except Exception as e:
            logger.warning(f"No se pudo mostrar el cuerpo de la respuesta: {str(e)}")
        
        return response.status_code, response.reason
        
    except requests.RequestException as e:
        logger.error(f"Error: {str(e)}")
        return None, str(e)

def main():
    """Función principal."""
    logger.info("Iniciando pruebas HTTP")
    
    # Base URL del servidor
    base_url = "https://waagentv1.onrender.com"
    
    # Lista de endpoints a probar
    endpoints = [
        "/",                # Raíz
        "/ws",              # Endpoint WebSocket
        "/api",             # API
        "/api/ws",          # API WebSocket
        "/health",          # Endpoint de salud
        "/status",          # Estado
    ]
    
    # Probar cada endpoint con y sin token
    results = []
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        
        # Probar sin token
        status_code, reason = test_http_endpoint(url, with_token=False)
        results.append((f"{endpoint} (sin token)", status_code, reason))
        
        # Probar con token
        status_code, reason = test_http_endpoint(url, with_token=True)
        results.append((f"{endpoint} (con token)", status_code, reason))
    
    # Mostrar resumen de resultados
    logger.info("\n=== RESUMEN DE PRUEBAS HTTP ===")
    
    for endpoint, status_code, reason in results:
        if status_code == 200:
            status = "✅ ÉXITO"
        elif status_code:
            status = f"❌ FALLO ({status_code})"
        else:
            status = f"❌ ERROR ({reason})"
        
        logger.info(f"{endpoint}: {status}")
    
    logger.info("Todas las pruebas completadas")

if __name__ == "__main__":
    # Deshabilitar advertencias de SSL no verificado
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    main()
