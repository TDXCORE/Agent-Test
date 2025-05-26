"""
Listeners de eventos para WebSockets.
Sistema completo de eventos en tiempo real con logging detallado.
"""

from typing import Dict, Any
import logging
from datetime import datetime
from .dispatcher import register_listener

logger = logging.getLogger(__name__)

def setup_listeners(connection_manager):
    """Configura todos los listeners de eventos."""
    
    logger.info("🔧 Configurando listeners de eventos WebSocket...")
    
    # Listener para nuevos mensajes
    @register_listener("new_message")
    async def on_new_message(data: Dict[str, Any]) -> None:
        """Notifica a los clientes cuando hay un nuevo mensaje."""
        conversation_id = data.get("conversation_id")
        message = data.get("message")
        
        logger.info(f"🔔 EVENTO: Nuevo mensaje recibido para conversación {conversation_id}")
        
        if not conversation_id or not message:
            logger.warning("❌ Datos incompletos en evento new_message")
            logger.warning(f"   - conversation_id: {conversation_id}")
            logger.warning(f"   - message: {message}")
            return
        
        # Estructura de evento estandarizada para el frontend
        event_payload = {
            "type": "event",
            "payload": {
                "type": "new_message",
                "data": {
                    "conversation_id": conversation_id,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        logger.info(f"📤 Enviando evento new_message a clientes de conversación {conversation_id}")
        
        # Enviar notificación a todos los clientes de la conversación
        await connection_manager.broadcast_to_conversation(
            conversation_id,
            event_payload
        )
        
        # También broadcast global para dashboard
        await connection_manager.broadcast_to_all({
            "type": "event",
            "payload": {
                "type": "global_new_message",
                "data": {
                    "conversation_id": conversation_id,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
            }
        })
        
        logger.info(f"✅ Evento new_message procesado exitosamente")
    
    # Listener para mensajes actualizados
    @register_listener("message_updated")
    async def on_message_updated(data: Dict[str, Any]) -> None:
        """Notifica a los clientes cuando se actualiza un mensaje."""
        conversation_id = data.get("conversation_id")
        message_id = data.get("message_id")
        message = data.get("message")
        
        logger.info(f"🔔 EVENTO: Mensaje actualizado {message_id} en conversación {conversation_id}")
        
        if not conversation_id or not message_id:
            logger.warning("❌ Datos incompletos en evento message_updated")
            return
        
        event_payload = {
            "type": "event",
            "payload": {
                "type": "message_updated",
                "data": {
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        logger.info(f"📤 Enviando evento message_updated a clientes de conversación {conversation_id}")
        
        await connection_manager.broadcast_to_conversation(
            conversation_id,
            event_payload
        )
        
        logger.info(f"✅ Evento message_updated procesado exitosamente")
    
    # Listener para mensajes marcados como leídos
    @register_listener("messages_read")
    async def on_messages_read(data: Dict[str, Any]) -> None:
        """Notifica a los clientes cuando se marcan mensajes como leídos."""
        conversation_id = data.get("conversation_id")
        count = data.get("count", 0)
        
        logger.info(f"🔔 EVENTO: {count} mensajes marcados como leídos en conversación {conversation_id}")
        
        if not conversation_id:
            logger.warning("❌ Datos incompletos en evento messages_read")
            return
        
        event_payload = {
            "type": "event",
            "payload": {
                "type": "messages_read",
                "data": {
                    "conversation_id": conversation_id,
                    "count": count,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        logger.info(f"📤 Enviando evento messages_read a clientes de conversación {conversation_id}")
        
        await connection_manager.broadcast_to_conversation(
            conversation_id,
            event_payload
        )
        
        # También broadcast global para actualizar contadores
        await connection_manager.broadcast_to_all({
            "type": "event",
            "payload": {
                "type": "global_messages_read",
                "data": {
                    "conversation_id": conversation_id,
                    "count": count,
                    "timestamp": datetime.now().isoformat()
                }
            }
        })
        
        logger.info(f"✅ Evento messages_read procesado exitosamente")
    
    # Listener para mensajes eliminados
    @register_listener("message_deleted")
    async def on_message_deleted(data: Dict[str, Any]) -> None:
        """Notifica a los clientes cuando se elimina un mensaje."""
        message_id = data.get("message_id")
        conversation_id = data.get("conversation_id")
        
        logger.info(f"🔔 EVENTO: Mensaje eliminado {message_id} en conversación {conversation_id}")
        
        if not message_id or not conversation_id:
            logger.warning("❌ Datos incompletos en evento message_deleted")
            return
        
        event_payload = {
            "type": "event",
            "payload": {
                "type": "message_deleted",
                "data": {
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        logger.info(f"📤 Enviando evento message_deleted a clientes de conversación {conversation_id}")
        
        await connection_manager.broadcast_to_conversation(
            conversation_id,
            event_payload
        )
        
        logger.info(f"✅ Evento message_deleted procesado exitosamente")
    
    # Listener para conversaciones creadas
    @register_listener("conversation_created")
    async def on_conversation_created(data: Dict[str, Any]) -> None:
        """Notifica a los clientes cuando se crea una nueva conversación."""
        conversation = data.get("conversation")
        
        logger.info(f"🔔 EVENTO: Nueva conversación creada {conversation.get('id') if conversation else 'N/A'}")
        
        if not conversation:
            logger.warning("❌ Datos incompletos en evento conversation_created")
            return
        
        event_payload = {
            "type": "event",
            "payload": {
                "type": "conversation_created",
                "data": {
                    "conversation": conversation,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        logger.info(f"📤 Enviando evento conversation_created a todos los clientes")
        
        # Broadcast global para nuevas conversaciones
        await connection_manager.broadcast_to_all(event_payload)
        
        logger.info(f"✅ Evento conversation_created procesado exitosamente")
    
    # Listener para actualizaciones de conversación
    @register_listener("conversation_updated")
    async def on_conversation_updated(data: Dict[str, Any]) -> None:
        """Notifica a los clientes cuando se actualiza una conversación."""
        conversation_id = data.get("conversation_id")
        conversation = data.get("conversation")
        
        logger.info(f"🔔 EVENTO: Conversación actualizada {conversation_id}")
        
        if not conversation_id:
            logger.warning("❌ Datos incompletos en evento conversation_updated")
            return
        
        event_payload = {
            "type": "event",
            "payload": {
                "type": "conversation_updated",
                "data": {
                    "conversation_id": conversation_id,
                    "conversation": conversation,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        logger.info(f"📤 Enviando evento conversation_updated a clientes de conversación {conversation_id}")
        
        await connection_manager.broadcast_to_conversation(
            conversation_id,
            event_payload
        )
        
        # También broadcast global para dashboard
        await connection_manager.broadcast_to_all({
            "type": "event",
            "payload": {
                "type": "global_conversation_updated",
                "data": {
                    "conversation_id": conversation_id,
                    "conversation": conversation,
                    "timestamp": datetime.now().isoformat()
                }
            }
        })
        
        logger.info(f"✅ Evento conversation_updated procesado exitosamente")
    
    # Listener para conversaciones archivadas
    @register_listener("conversation_archived")
    async def on_conversation_archived(data: Dict[str, Any]) -> None:
        """Notifica a los clientes cuando se archiva una conversación."""
        conversation_id = data.get("conversation_id")
        conversation = data.get("conversation")
        
        logger.info(f"🔔 EVENTO: Conversación archivada {conversation_id}")
        
        if not conversation_id:
            logger.warning("❌ Datos incompletos en evento conversation_archived")
            return
        
        event_payload = {
            "type": "event",
            "payload": {
                "type": "conversation_archived",
                "data": {
                    "conversation_id": conversation_id,
                    "conversation": conversation,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        logger.info(f"📤 Enviando evento conversation_archived a todos los clientes")
        
        # Broadcast global para conversaciones archivadas
        await connection_manager.broadcast_to_all(event_payload)
        
        logger.info(f"✅ Evento conversation_archived procesado exitosamente")
    
    # Listener para cambios de estado del agente
    @register_listener("agent_toggled")
    async def on_agent_toggled(data: Dict[str, Any]) -> None:
        """Notifica a los clientes cuando se cambia el estado del agente."""
        conversation_id = data.get("conversation_id")
        agent_enabled = data.get("agent_enabled")
        conversation = data.get("conversation")
        
        logger.info(f"🔔 EVENTO: Agente {'habilitado' if agent_enabled else 'deshabilitado'} en conversación {conversation_id}")
        
        if not conversation_id or agent_enabled is None:
            logger.warning("❌ Datos incompletos en evento agent_toggled")
            return
        
        event_payload = {
            "type": "event",
            "payload": {
                "type": "agent_toggled",
                "data": {
                    "conversation_id": conversation_id,
                    "agent_enabled": agent_enabled,
                    "conversation": conversation,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        logger.info(f"📤 Enviando evento agent_toggled a clientes de conversación {conversation_id}")
        
        await connection_manager.broadcast_to_conversation(
            conversation_id,
            event_payload
        )
        
        # También broadcast global para dashboard
        await connection_manager.broadcast_to_all({
            "type": "event",
            "payload": {
                "type": "global_agent_toggled",
                "data": {
                    "conversation_id": conversation_id,
                    "agent_enabled": agent_enabled,
                    "conversation": conversation,
                    "timestamp": datetime.now().isoformat()
                }
            }
        })
        
        logger.info(f"✅ Evento agent_toggled procesado exitosamente")
    
    # Listener genérico para debugging
    @register_listener("debug_event")
    async def on_debug_event(data: Dict[str, Any]) -> None:
        """Listener genérico para eventos de debugging."""
        event_type = data.get("event_type", "unknown")
        
        logger.info(f"🔔 EVENTO DEBUG: {event_type}")
        logger.info(f"   Datos: {data}")
        
        event_payload = {
            "type": "event",
            "payload": {
                "type": "debug_event",
                "data": {
                    "event_type": event_type,
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                }
            }
        }
        
        # Broadcast global para eventos de debug
        await connection_manager.broadcast_to_all(event_payload)
        
        logger.info(f"✅ Evento debug procesado exitosamente")
    
    logger.info("✅ Todos los listeners de eventos configurados exitosamente")
    logger.info("📋 Listeners registrados:")
    logger.info("   - new_message")
    logger.info("   - message_updated")
    logger.info("   - messages_read")
    logger.info("   - message_deleted")
    logger.info("   - conversation_created")
    logger.info("   - conversation_updated")
    logger.info("   - conversation_archived")
    logger.info("   - agent_toggled")
    logger.info("   - debug_event")
