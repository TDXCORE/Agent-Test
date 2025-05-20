"""
Punto de entrada principal para el módulo WebSockets.
"""

import logging
from fastapi import FastAPI, APIRouter
from .setup import setup_websockets
from .connection import ConnectionManager
from .events.dispatcher import dispatch_event

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Instancia global del gestor de conexiones
connection_manager = ConnectionManager()

def init_websockets(app: FastAPI) -> None:
    """
    Inicializa el módulo WebSockets en la aplicación FastAPI.
    
    Args:
        app: Instancia de FastAPI donde se registrarán los endpoints WebSocket
    """
    logger.info("Inicializando módulo WebSockets")
    
    # Configurar WebSockets en la aplicación
    setup_websockets(app)
    
    logger.info("Módulo WebSockets inicializado correctamente")

def get_connection_manager() -> ConnectionManager:
    """
    Obtiene la instancia global del gestor de conexiones.
    
    Returns:
        Instancia de ConnectionManager
    """
    return connection_manager

async def notify_event(event_type: str, data: dict) -> None:
    """
    Notifica un evento a través del sistema de eventos.
    
    Args:
        event_type: Tipo de evento a notificar
        data: Datos del evento
    """
    await dispatch_event(event_type, data)
