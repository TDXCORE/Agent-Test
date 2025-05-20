"""
Sistema de eventos para WebSockets.
Permite la comunicación desacoplada entre componentes.
"""

from typing import Dict, Any, Callable, List, Awaitable
import asyncio
import logging

logger = logging.getLogger(__name__)

# Tipo para listeners: función asíncrona que recibe datos de evento
EventListener = Callable[[Dict[str, Any]], Awaitable[None]]

# Registro de listeners por tipo de evento
_event_listeners: Dict[str, List[EventListener]] = {}

def register_listener(event_type: str, listener: EventListener) -> None:
    """Registra un listener para un tipo de evento específico."""
    if event_type not in _event_listeners:
        _event_listeners[event_type] = []
    
    _event_listeners[event_type].append(listener)
    logger.info(f"Registrado listener para evento '{event_type}'")

async def dispatch_event(event_type: str, data: Dict[str, Any]) -> None:
    """Dispara un evento notificando a todos los listeners registrados."""
    if event_type not in _event_listeners:
        return
    
    listeners = _event_listeners[event_type]
    logger.debug(f"Disparando evento '{event_type}' a {len(listeners)} listeners")
    
    # Ejecutar todos los listeners concurrentemente
    await asyncio.gather(
        *[listener(data) for listener in listeners],
        return_exceptions=True  # Evitar que un error en un listener afecte a otros
    )
