"""
Autenticación para conexiones WebSocket.
"""

import os
from typing import Tuple, Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

logger = logging.getLogger(__name__)

# Obtener el token de autenticación de las variables de entorno
WEBSOCKET_AUTH_TOKEN = os.getenv("WEBSOCKET_AUTH_TOKEN")

async def verify_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Verifica un token de autenticación.
    
    Args:
        token: El token a verificar
        
    Returns:
        Tupla (is_valid, user_data) donde:
        - is_valid: Booleano indicando si el token es válido
        - user_data: Datos del usuario si el token es válido, None en caso contrario
    """
    # Verificar si el token está presente
    if not token:
        logger.warning("Intento de conexión sin token")
        return False, None
    
    # En desarrollo, si no hay token configurado, aceptar cualquier token
    if not WEBSOCKET_AUTH_TOKEN:
        logger.warning("WEBSOCKET_AUTH_TOKEN no está configurado. Usando verificación simulada. NO USAR EN PRODUCCIÓN.")
        return True, {"user_id": token}
    
    # En producción, verificar que el token coincida exactamente
    if token == WEBSOCKET_AUTH_TOKEN:
        logger.info("Token de WebSocket válido")
        return True, {"user_id": "system"}
    
    # Si llegamos aquí, el token es inválido
    logger.warning(f"Token de WebSocket inválido: {token[:10]}...")
    return False, None
