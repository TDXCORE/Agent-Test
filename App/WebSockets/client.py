"""
Cliente WebSocket para conectarse desde el frontend.
"""

import json
import logging
import uuid
from typing import Dict, Any, Optional, Callable, List, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketClient:
    """
    Cliente WebSocket para conectarse al servidor.
    
    Esta clase está diseñada para ser utilizada en el frontend para
    facilitar la comunicación con el servidor WebSocket.
    """
    
    def __init__(self, url: str, token: Optional[str] = None):
        """
        Inicializa el cliente WebSocket.
        
        Args:
            url: URL del servidor WebSocket
            token: Token de autenticación (opcional)
        """
        self.url = url
        self.token = token
        self.socket = None
        self.connected = False
        self.client_id = None
        self.user_id = None
        
        # Callbacks
        self.on_connect = None
        self.on_disconnect = None
        self.on_error = None
        self.on_message = None
        
        # Callbacks específicos por tipo de evento
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # Callbacks para respuestas a mensajes específicos
        self.response_handlers: Dict[str, Callable] = {}
    
    def connect(self) -> None:
        """Conecta al servidor WebSocket."""
        # Construir URL con token si está disponible
        full_url = self.url
        if self.token:
            if "?" in full_url:
                full_url += f"&token={self.token}"
            else:
                full_url += f"?token={self.token}"
        
        try:
            # Nota: Esta es una implementación conceptual.
            # En un cliente real, aquí se usaría la API WebSocket del navegador
            # o una biblioteca como socket.io-client
            self.socket = {"url": full_url, "connected": True}
            self.connected = True
            
            # Simular evento de conexión
            if self.on_connect:
                self.on_connect({
                    "client_id": str(uuid.uuid4()),
                    "timestamp": datetime.now().isoformat()
                })
            
            logger.info(f"Conectado a {full_url}")
        
        except Exception as e:
            logger.error(f"Error al conectar: {str(e)}")
            if self.on_error:
                self.on_error({
                    "code": "connection_error",
                    "message": f"Error al conectar: {str(e)}"
                })
    
    def disconnect(self) -> None:
        """Desconecta del servidor WebSocket."""
        if not self.connected:
            return
        
        try:
            # Nota: En un cliente real, aquí se cerraría la conexión WebSocket
            self.socket = None
            self.connected = False
            
            # Simular evento de desconexión
            if self.on_disconnect:
                self.on_disconnect({
                    "timestamp": datetime.now().isoformat()
                })
            
            logger.info("Desconectado")
        
        except Exception as e:
            logger.error(f"Error al desconectar: {str(e)}")
    
    def send(self, resource: str, action: str, data: Dict[str, Any], 
            callback: Optional[Callable] = None) -> str:
        """
        Envía un mensaje al servidor.
        
        Args:
            resource: Tipo de recurso (conversations, messages, users)
            action: Acción a realizar (get_all, get_by_id, create, update, delete)
            data: Datos del mensaje
            callback: Función a llamar cuando se reciba la respuesta
            
        Returns:
            ID del mensaje enviado
        """
        if not self.connected:
            raise ValueError("No conectado al servidor")
        
        # Generar ID único para el mensaje
        message_id = str(uuid.uuid4())
        
        # Construir mensaje
        message = {
            "type": "request",
            "id": message_id,
            "resource": resource,
            "payload": {
                "action": action,
                **data
            }
        }
        
        # Registrar callback para la respuesta si se proporcionó
        if callback:
            self.response_handlers[message_id] = callback
        
        # Enviar mensaje
        # Nota: En un cliente real, aquí se enviaría el mensaje por WebSocket
        logger.info(f"Enviando mensaje: {json.dumps(message)}")
        
        return message_id
    
    def on(self, event_type: str, callback: Callable) -> None:
        """
        Registra un callback para un tipo de evento específico.
        
        Args:
            event_type: Tipo de evento (new_message, message_deleted, etc.)
            callback: Función a llamar cuando se reciba el evento
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(callback)
    
    def off(self, event_type: str, callback: Optional[Callable] = None) -> None:
        """
        Elimina un callback para un tipo de evento específico.
        
        Args:
            event_type: Tipo de evento
            callback: Callback a eliminar. Si es None, elimina todos los callbacks.
        """
        if event_type not in self.event_handlers:
            return
        
        if callback is None:
            self.event_handlers[event_type] = []
        else:
            self.event_handlers[event_type] = [
                cb for cb in self.event_handlers[event_type] if cb != callback
            ]
    
    def _handle_message(self, message: Dict[str, Any]) -> None:
        """
        Maneja un mensaje recibido del servidor.
        
        Args:
            message: Mensaje recibido
        """
        message_type = message.get("type")
        message_id = message.get("id")
        payload = message.get("payload", {})
        
        # Llamar al callback general si está definido
        if self.on_message:
            self.on_message(message)
        
        # Manejar según tipo de mensaje
        if message_type == "connected":
            self.client_id = payload.get("client_id")
            self.user_id = payload.get("user_id")
            
            if self.on_connect:
                self.on_connect(payload)
        
        elif message_type == "error":
            if self.on_error:
                self.on_error(payload)
            
            # Si hay un callback registrado para este mensaje, llamarlo con el error
            if message_id in self.response_handlers:
                callback = self.response_handlers.pop(message_id)
                callback(None, payload)
        
        elif message_type == "response":
            # Si hay un callback registrado para este mensaje, llamarlo con la respuesta
            if message_id in self.response_handlers:
                callback = self.response_handlers.pop(message_id)
                callback(payload, None)
        
        elif message_type == "event":
            event_type = payload.get("type")
            event_data = payload.get("data", {})
            
            # Llamar a los callbacks registrados para este tipo de evento
            if event_type in self.event_handlers:
                for callback in self.event_handlers[event_type]:
                    try:
                        callback(event_data)
                    except Exception as e:
                        logger.error(f"Error en callback de evento {event_type}: {str(e)}")

# Ejemplo de uso:
"""
// En el frontend (JavaScript)
const client = new WebSocketClient('ws://localhost:8000/ws', 'mi-token-jwt');

// Registrar callbacks
client.on_connect = (data) => {
    console.log('Conectado:', data);
};

client.on_disconnect = (data) => {
    console.log('Desconectado:', data);
};

client.on_error = (error) => {
    console.error('Error:', error);
};

// Registrar callback para eventos específicos
client.on('new_message', (message) => {
    console.log('Nuevo mensaje:', message);
    // Actualizar UI
});

// Conectar
client.connect();

// Enviar mensaje
client.send('conversations', 'get_all', { user_id: 'user123' }, (data, error) => {
    if (error) {
        console.error('Error al obtener conversaciones:', error);
        return;
    }
    
    console.log('Conversaciones:', data.conversations);
    // Actualizar UI
});

// Desconectar cuando se cierre la página
window.addEventListener('beforeunload', () => {
    client.disconnect();
});
"""
