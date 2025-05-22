"""
Gestor de conexiones WebSocket.
Mantiene un registro de todas las conexiones activas y proporciona métodos para enviar mensajes.
"""

from fastapi import WebSocket
from typing import Dict, List, Set, Optional, Any
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Todas las conexiones activas
        self.active_connections: Set[WebSocket] = set()
        
        # Conexiones agrupadas por diferentes criterios
        self.connections_by_user: Dict[str, List[WebSocket]] = {}
        self.connections_by_conversation: Dict[str, List[WebSocket]] = {}
        self.connections_by_client: Dict[str, WebSocket] = {}
        
        # Metadatos de conexión
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        
        # Timestamp de último mensaje por conexión
        self.last_activity: Dict[WebSocket, datetime] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str, 
                     user_id: Optional[str] = None, 
                     conversation_id: Optional[str] = None) -> None:
        """Establece una nueva conexión WebSocket."""
        # Aceptar conexión
        await websocket.accept()
        
        # Registrar conexión
        self.active_connections.add(websocket)
        self.connections_by_client[client_id] = websocket
        self.last_activity[websocket] = datetime.now()
        
        # Almacenar metadatos
        self.connection_metadata[websocket] = {
            "client_id": client_id,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "connected_at": datetime.now()
        }
        
        # Registrar en grupos si se proporcionan IDs
        if user_id:
            if user_id not in self.connections_by_user:
                self.connections_by_user[user_id] = []
            self.connections_by_user[user_id].append(websocket)
        
        if conversation_id:
            if conversation_id not in self.connections_by_conversation:
                self.connections_by_conversation[conversation_id] = []
            self.connections_by_conversation[conversation_id].append(websocket)
        
        logger.info(f"Cliente {client_id} conectado. Total conexiones: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket) -> None:
        """Maneja la desconexión de un WebSocket."""
        # Obtener metadatos antes de eliminar
        metadata = self.connection_metadata.get(websocket, {})
        client_id = metadata.get("client_id")
        user_id = metadata.get("user_id")
        conversation_id = metadata.get("conversation_id")
        
        # Eliminar de todas las colecciones
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if client_id and client_id in self.connections_by_client:
            del self.connections_by_client[client_id]
        
        if user_id and user_id in self.connections_by_user:
            if websocket in self.connections_by_user[user_id]:
                self.connections_by_user[user_id].remove(websocket)
            if not self.connections_by_user[user_id]:
                del self.connections_by_user[user_id]
        
        if conversation_id and conversation_id in self.connections_by_conversation:
            if websocket in self.connections_by_conversation[conversation_id]:
                self.connections_by_conversation[conversation_id].remove(websocket)
            if not self.connections_by_conversation[conversation_id]:
                del self.connections_by_conversation[conversation_id]
        
        # Limpiar metadatos y actividad
        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]
        
        if websocket in self.last_activity:
            del self.last_activity[websocket]
        
        logger.info(f"Cliente {client_id} desconectado. Total conexiones: {len(self.active_connections)}")
    
    async def send_json(self, websocket: WebSocket, message: Dict[str, Any]) -> bool:
        """Envía un mensaje JSON a una conexión específica."""
        # Verificar si el websocket está en las conexiones activas
        if websocket not in self.active_connections:
            logger.warning("Intento de enviar mensaje a una conexión inactiva")
            return False
            
        try:
            # Verificar si el websocket está en estado cerrado
            if getattr(websocket, "_closed", False):
                logger.warning("Intento de enviar mensaje a una conexión cerrada")
                self.disconnect(websocket)
                return False
                
            await websocket.send_json(message)
            self.last_activity[websocket] = datetime.now()
            return True
        except Exception as e:
            logger.error(f"Error al enviar mensaje: {str(e)}")
            # Si hay un error al enviar, desconectar el websocket
            self.disconnect(websocket)
            return False
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Envía un mensaje a todas las conexiones activas."""
        if not self.active_connections:
            return
        
        # Crear una copia de las conexiones activas para evitar modificar durante la iteración
        active_connections = set(self.active_connections)
        failed_connections = []
        
        for websocket in active_connections:
            # Verificar si el websocket está en estado cerrado
            if getattr(websocket, "_closed", False):
                failed_connections.append(websocket)
                continue
                
            try:
                await websocket.send_json(message)
                self.last_activity[websocket] = datetime.now()
            except Exception as e:
                logger.error(f"Error al enviar broadcast: {str(e)}")
                failed_connections.append(websocket)
        
        # Limpiar conexiones fallidas
        for websocket in failed_connections:
            if websocket in self.active_connections:  # Verificar nuevamente por si acaso
                self.disconnect(websocket)
    
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]) -> None:
        """Envía un mensaje a todas las conexiones de un usuario."""
        if user_id not in self.connections_by_user:
            return
        
        # Crear una copia de las conexiones del usuario para evitar modificar durante la iteración
        user_connections = list(self.connections_by_user[user_id])
        failed_connections = []
        
        for websocket in user_connections:
            # Verificar si el websocket está en estado cerrado
            if getattr(websocket, "_closed", False):
                failed_connections.append(websocket)
                continue
                
            try:
                await websocket.send_json(message)
                self.last_activity[websocket] = datetime.now()
            except Exception as e:
                logger.error(f"Error al enviar a usuario {user_id}: {str(e)}")
                failed_connections.append(websocket)
        
        # Limpiar conexiones fallidas
        for websocket in failed_connections:
            if websocket in self.active_connections:  # Verificar nuevamente por si acaso
                self.disconnect(websocket)
    
    async def broadcast_to_conversation(self, conversation_id: str, message: Dict[str, Any]) -> None:
        """Envía un mensaje a todas las conexiones de una conversación."""
        if conversation_id not in self.connections_by_conversation:
            return
        
        # Crear una copia de las conexiones de la conversación para evitar modificar durante la iteración
        conversation_connections = list(self.connections_by_conversation[conversation_id])
        failed_connections = []
        
        for websocket in conversation_connections:
            # Verificar si el websocket está en estado cerrado
            if getattr(websocket, "_closed", False):
                failed_connections.append(websocket)
                continue
                
            try:
                await websocket.send_json(message)
                self.last_activity[websocket] = datetime.now()
            except Exception as e:
                logger.error(f"Error al enviar a conversación {conversation_id}: {str(e)}")
                failed_connections.append(websocket)
        
        # Limpiar conexiones fallidas
        for websocket in failed_connections:
            if websocket in self.active_connections:  # Verificar nuevamente por si acaso
                self.disconnect(websocket)
    
    def get_connection_count(self) -> int:
        """Retorna el número total de conexiones activas."""
        return len(self.active_connections)
    
    def get_user_connection_count(self, user_id: str) -> int:
        """Retorna el número de conexiones para un usuario específico."""
        if user_id not in self.connections_by_user:
            return 0
        return len(self.connections_by_user[user_id])
    
    def get_conversation_connection_count(self, conversation_id: str) -> int:
        """Retorna el número de conexiones para una conversación específica."""
        if conversation_id not in self.connections_by_conversation:
            return 0
        return len(self.connections_by_conversation[conversation_id])
