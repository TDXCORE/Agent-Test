"""
Autenticación para conexiones WebSocket.
"""

from typing import Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

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
    # TODO: Implementar verificación real de tokens
    # Por ahora, aceptamos cualquier token para desarrollo
    logger.warning("Usando verificación de tokens simulada. NO USAR EN PRODUCCIÓN.")
    
    if not token:
        return False, None
    
    # Simulación: token es el user_id
    return True, {"user_id": token}
