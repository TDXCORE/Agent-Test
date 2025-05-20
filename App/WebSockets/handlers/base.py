"""
Handler base para mensajes WebSocket.
"""

from typing import Dict, Any, Optional, List, Callable, Awaitable
from fastapi import WebSocket
import logging
import json
import traceback
from ..models.base import WebSocketMessage, ErrorResponse, MessageType

logger = logging.getLogger(__name__)

class BaseHandler:
    """Clase base para todos los handlers de WebSocket."""
    
    def __init__(self, connection_manager):
        """Inicializa el handler."""
        self.connection_manager = connection_manager
        self.action_handlers: Dict[str, Callable] = {}
        self._register_actions()
    
    def _register_actions(self) -> None:
        """Registra los manejadores de acciones."""
        # Debe ser implementado por las subclases
        pass
    
    async def handle_message(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Maneja un mensaje entrante."""
        try:
            # Validar mensaje
            ws_message = WebSocketMessage(**message)
            
            # Procesar según tipo de mensaje
            if ws_message.type == MessageType.REQUEST:
                await self._handle_request(websocket, ws_message)
            else:
                logger.warning(f"Tipo de mensaje no soportado: {ws_message.type}")
                await self._send_error(
                    websocket, 
                    ws_message.id, 
                    "unsupported_message_type", 
                    f"Tipo de mensaje no soportado: {ws_message.type}"
                )
        
        except Exception as e:
            logger.error(f"Error al procesar mensaje: {str(e)}")
            logger.debug(traceback.format_exc())
            
            # Intentar obtener ID del mensaje para la respuesta
            message_id = message.get("id", "unknown")
            
            await self._send_error(
                websocket,
                message_id,
                "message_processing_error",
                f"Error al procesar mensaje: {str(e)}"
            )
    
    async def _handle_request(self, websocket: WebSocket, message: WebSocketMessage) -> None:
        """Maneja una solicitud de recurso."""
        payload = message.payload
        action = payload.get("action")
        
        if not action:
            await self._send_error(
                websocket,
                message.id,
                "missing_action",
                "La solicitud debe incluir una acción"
            )
            return
        
        # Buscar handler para la acción
        handler = self.action_handlers.get(action)
        
        if not handler:
            await self._send_error(
                websocket,
                message.id,
                "unknown_action",
                f"Acción desconocida: {action}"
            )
            return
        
        # Ejecutar handler
        try:
            result = await handler(payload)
            await self._send_response(websocket, message.id, result)
        
        except Exception as e:
            logger.error(f"Error al ejecutar acción {action}: {str(e)}")
            logger.debug(traceback.format_exc())
            
            await self._send_error(
                websocket,
                message.id,
                "action_execution_error",
                f"Error al ejecutar acción {action}: {str(e)}"
            )
    
    async def _send_response(self, websocket: WebSocket, message_id: str, data: Any) -> None:
        """Envía una respuesta al cliente."""
        response = {
            "type": MessageType.RESPONSE,
            "id": message_id,
            "payload": data
        }
        
        await self.connection_manager.send_json(websocket, response)
    
    async def _send_error(self, websocket: WebSocket, message_id: str, 
                         code: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Envía un mensaje de error al cliente."""
        error = ErrorResponse(
            code=code,
            message=message,
            details=details
        )
        
        response = {
            "type": MessageType.ERROR,
            "id": message_id,
            "payload": error.dict()
        }
        
        await self.connection_manager.send_json(websocket, response)
