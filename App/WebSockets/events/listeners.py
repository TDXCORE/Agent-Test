"""
Listeners de eventos para WebSockets.
"""

from typing import Dict, Any
import logging
from .dispatcher import register_listener

logger = logging.getLogger(__name__)

def setup_listeners(connection_manager):
    """Configura todos los listeners de eventos."""
    
    # Listener para nuevos mensajes
    @register_listener("new_message")
    async def on_new_message(data: Dict[str, Any]) -> None:
        """Notifica a los clientes cuando hay un nuevo mensaje."""
        conversation_id = data.get("conversation_id")
        message = data.get("message")
        
        if not conversation_id or not message:
            logger.warning("Datos incompletos en evento new_message")
            return
        
        # Enviar notificación a todos los clientes de la conversación
        await connection_manager.broadcast_to_conversation(
            conversation_id,
            {
                "type": "new_message",
                "data": message
            }
        )
    
    # Listener para mensajes eliminados
    @register_listener("message_deleted")
    async def on_message_deleted(data: Dict[str, Any]) -> None:
        """Notifica a los clientes cuando se elimina un mensaje."""
        message_id = data.get("message_id")
        conversation_id = data.get("conversation_id")
        
        if not message_id or not conversation_id:
            logger.warning("Datos incompletos en evento message_deleted")
            return
        
        # Enviar notificación a todos los clientes de la conversación
        await connection_manager.broadcast_to_conversation(
            conversation_id,
            {
                "type": "message_deleted",
                "data": {"message_id": message_id}
            }
        )
    
    # Listener para actualizaciones de conversación
    @register_listener("conversation_updated")
    async def on_conversation_updated(data: Dict[str, Any]) -> None:
        """Notifica a los clientes cuando se actualiza una conversación."""
        conversation_id = data.get("conversation_id")
        conversation = data.get("conversation")
        
        if not conversation_id or not conversation:
            logger.warning("Datos incompletos en evento conversation_updated")
            return
        
        # Enviar notificación a todos los clientes de la conversación
        await connection_manager.broadcast_to_conversation(
            conversation_id,
            {
                "type": "conversation_updated",
                "data": conversation
            }
        )
