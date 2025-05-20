"""
Pruebas para el módulo WebSockets.
"""

import asyncio
import json
import logging
import pytest
import websockets
import uuid
import sys
import os
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Añadir directorio raíz al path para poder importar App
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar módulos a probar
from App.WebSockets.main import init_websockets
from App.WebSockets.connection import ConnectionManager
from App.WebSockets.events.dispatcher import dispatch_event, register_listener

# Crear aplicación de prueba
app = FastAPI()
init_websockets(app)

# Cliente de prueba
client = TestClient(app)

# Clase para cliente WebSocket de prueba
class TestWebSocketClient:
    def __init__(self, url, token=None):
        self.url = url
        self.token = token
        self.connection = None
        self.messages = []
        self.connected = False
    
    async def connect(self):
        """Conecta al servidor WebSocket."""
        full_url = self.url
        if self.token:
            if "?" in full_url:
                full_url += f"&token={self.token}"
            else:
                full_url += f"?token={self.token}"
        
        self.connection = await websockets.connect(full_url)
        self.connected = True
        logger.info(f"Conectado a {full_url}")
    
    async def disconnect(self):
        """Desconecta del servidor WebSocket."""
        if self.connection:
            await self.connection.close()
            self.connected = False
            logger.info("Desconectado")
    
    async def send(self, message):
        """Envía un mensaje al servidor."""
        if not self.connected:
            raise ValueError("No conectado al servidor")
        
        await self.connection.send(json.dumps(message))
        logger.info(f"Mensaje enviado: {message}")
    
    async def receive(self):
        """Recibe un mensaje del servidor."""
        if not self.connected:
            raise ValueError("No conectado al servidor")
        
        message = await self.connection.recv()
        parsed = json.loads(message)
        self.messages.append(parsed)
        logger.info(f"Mensaje recibido: {parsed}")
        return parsed
    
    async def send_request(self, resource, action, data):
        """Envía una solicitud al servidor y espera la respuesta."""
        message_id = str(uuid.uuid4())
        
        # Enviar solicitud
        await self.send({
            "type": "request",
            "id": message_id,
            "resource": resource,
            "payload": {
                "action": action,
                **data
            }
        })
        
        # Esperar respuesta
        while True:
            response = await self.receive()
            if response.get("id") == message_id:
                return response
    
    async def listen(self, timeout=1):
        """Escucha mensajes durante un tiempo determinado."""
        try:
            while True:
                # Esperar mensaje con timeout
                message = await asyncio.wait_for(self.connection.recv(), timeout)
                parsed = json.loads(message)
                self.messages.append(parsed)
                logger.info(f"Mensaje recibido: {parsed}")
        except asyncio.TimeoutError:
            # Timeout esperado
            pass
        except Exception as e:
            logger.error(f"Error al escuchar mensajes: {str(e)}")

# Fixtures para pruebas
@pytest.fixture
def event_loop():
    """Fixture para obtener un event loop."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def ws_client():
    """Fixture para obtener un cliente WebSocket."""
    client = TestWebSocketClient("ws://localhost:8000/ws")
    await client.connect()
    yield client
    await client.disconnect()

# Pruebas
@pytest.mark.asyncio
async def test_connection(ws_client):
    """Prueba la conexión al servidor WebSocket."""
    # Esperar mensaje de bienvenida
    welcome = await ws_client.receive()
    
    # Verificar que es un mensaje de tipo "connected"
    assert welcome["type"] == "connected"
    assert "client_id" in welcome["payload"]

@pytest.mark.asyncio
async def test_conversations_get_all(ws_client):
    """Prueba la obtención de todas las conversaciones."""
    # Enviar solicitud
    response = await ws_client.send_request("conversations", "get_all", {
        "user_id": "test_user"
    })
    
    # Verificar respuesta
    assert response["type"] == "response"
    assert "conversations" in response["payload"]

@pytest.mark.asyncio
async def test_create_message(ws_client):
    """Prueba la creación de un mensaje."""
    # Enviar solicitud
    response = await ws_client.send_request("messages", "create", {
        "message": {
            "conversation_id": "test_conversation",
            "content": "Mensaje de prueba",
            "sender_id": "test_user"
        }
    })
    
    # Verificar respuesta
    assert response["type"] == "response"
    assert "message" in response["payload"]
    assert response["payload"]["message"]["content"] == "Mensaje de prueba"

@pytest.mark.asyncio
async def test_event_notification():
    """Prueba la notificación de eventos."""
    # Crear dos clientes
    client1 = TestWebSocketClient("ws://localhost:8000/ws")
    client2 = TestWebSocketClient("ws://localhost:8000/ws")
    
    try:
        # Conectar clientes
        await client1.connect()
        await client2.connect()
        
        # Esperar mensajes de bienvenida
        await client1.receive()
        await client2.receive()
        
        # Suscribir a conversación
        conversation_id = "test_conversation"
        
        # Cliente 1 crea un mensaje
        await client1.send_request("messages", "create", {
            "message": {
                "conversation_id": conversation_id,
                "content": "Hola desde cliente 1",
                "sender_id": "user1"
            }
        })
        
        # Cliente 2 debería recibir notificación
        # Escuchar mensajes durante 2 segundos
        await client2.listen(2)
        
        # Verificar que se recibió el evento
        events = [msg for msg in client2.messages if msg["type"] == "event"]
        assert len(events) > 0
        
        # Verificar que hay un evento de tipo "new_message"
        new_message_events = [
            evt for evt in events 
            if evt["payload"]["type"] == "new_message"
        ]
        assert len(new_message_events) > 0
        
        # Verificar contenido del mensaje
        message_data = new_message_events[0]["payload"]["data"]
        assert message_data["content"] == "Hola desde cliente 1"
        assert message_data["conversation_id"] == conversation_id
    
    finally:
        # Desconectar clientes
        await client1.disconnect()
        await client2.disconnect()

@pytest.mark.asyncio
async def test_error_handling(ws_client):
    """Prueba el manejo de errores."""
    # Enviar solicitud con recurso desconocido
    response = await ws_client.send_request("unknown_resource", "get_all", {})
    
    # Verificar respuesta de error
    assert response["type"] == "error"
    assert "code" in response["payload"]
    assert "message" in response["payload"]

@pytest.mark.asyncio
async def test_connection_manager():
    """Prueba el gestor de conexiones directamente."""
    # Crear gestor de conexiones
    manager = ConnectionManager()
    
    # Verificar estado inicial
    assert manager.get_connection_count() == 0
    
    # No podemos probar completamente sin WebSockets reales,
    # pero podemos verificar algunos métodos
    assert manager.get_user_connection_count("test_user") == 0
    assert manager.get_conversation_connection_count("test_conversation") == 0

@pytest.mark.asyncio
async def test_event_dispatcher():
    """Prueba el dispatcher de eventos."""
    # Crear variable para verificar que se llamó al listener
    event_received = False
    event_data = None
    
    # Registrar listener
    @register_listener("test_event")
    async def test_listener(data):
        nonlocal event_received, event_data
        event_received = True
        event_data = data
    
    # Disparar evento
    test_payload = {"message": "Hola mundo"}
    await dispatch_event("test_event", test_payload)
    
    # Verificar que se llamó al listener
    assert event_received
    assert event_data == test_payload

# Ejecutar pruebas
if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
