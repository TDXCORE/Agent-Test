"""
Script para probar el WebSocket desplegado en producción.
Este script se conecta a un servidor WebSocket remoto y ejecuta pruebas para verificar su funcionamiento.
"""

import asyncio
import json
import logging
import websockets
import uuid
import ssl
import sys
import argparse
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener token de WebSocket
WEBSOCKET_AUTH_TOKEN = os.getenv("WEBSOCKET_AUTH_TOKEN")

# Añadir directorio raíz al path para poder importar App
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RemoteWebSocketTester:
    def __init__(self, base_url, token=None, secure=True, timeout=10):
        self.base_url = base_url
        self.token = token
        self.secure = secure
        self.protocol = "wss" if secure else "ws"
        self.ws_url = f"{self.protocol}://{self.base_url}/ws"
        if self.token:
            self.ws_url += f"?token={self.token}"
        self.connection = None
        self.connected = False
        self.test_results = []
        self.timeout = timeout
        self.test_conversation_id = None
        self.test_message_id = None
        self.test_user_id = "test_user_" + str(uuid.uuid4())[:8]
    
    async def connect(self):
        """Conecta al servidor WebSocket."""
        logger.info(f"Conectando a {self.ws_url}...")
        
        try:
            # Configurar contexto SSL para conexiones seguras
            ssl_context = None
            if self.secure:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            # Conectar al WebSocket
            self.connection = await asyncio.wait_for(
                websockets.connect(
                    self.ws_url,
                    ssl=ssl_context,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=10
                ),
                timeout=self.timeout
            )
            
            self.connected = True
            logger.info("Conexión establecida")
            
            # Esperar mensaje de bienvenida
            welcome = await asyncio.wait_for(
                self.connection.recv(),
                timeout=self.timeout
            )
            welcome_data = json.loads(welcome)
            logger.info(f"Mensaje de bienvenida recibido: {welcome_data}")
            
            # Guardar client_id si está disponible
            if "payload" in welcome_data and "client_id" in welcome_data["payload"]:
                self.client_id = welcome_data["payload"]["client_id"]
                logger.info(f"ID de cliente asignado: {self.client_id}")
            
            return True
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout al conectar a {self.ws_url}")
            self.add_test_result("connection", False, "Timeout al conectar")
            return False
            
        except Exception as e:
            logger.error(f"Error al conectar: {str(e)}")
            self.add_test_result("connection", False, f"Error: {str(e)}")
            return False
    
    async def disconnect(self):
        """Desconecta del servidor WebSocket."""
        if self.connection:
            await self.connection.close()
            self.connected = False
            logger.info("Desconectado")
    
    async def send_request(self, resource, action, data=None):
        """Envía una solicitud al servidor y espera la respuesta."""
        if not self.connected:
            logger.error("No conectado al servidor")
            return None
        
        # Generar ID único para el mensaje
        message_id = str(uuid.uuid4())
        
        # Crear mensaje de solicitud
        request = {
            "type": "request",
            "id": message_id,
            "resource": resource,
            "payload": {
                "action": action,
                **(data or {})
            }
        }
        
        logger.info(f"Enviando solicitud: {request}")
        
        try:
            # Enviar solicitud
            await self.connection.send(json.dumps(request))
            
            # Esperar respuesta con timeout
            start_time = time.time()
            while True:
                if time.time() - start_time > self.timeout:
                    raise asyncio.TimeoutError("Timeout esperando respuesta")
                
                response_raw = await asyncio.wait_for(
                    self.connection.recv(),
                    timeout=self.timeout
                )
                response = json.loads(response_raw)
                
                # Verificar si es la respuesta a nuestra solicitud
                if response.get("id") == message_id:
                    logger.info(f"Respuesta recibida: {response}")
                    return response
                else:
                    # Si no es nuestra respuesta, podría ser un evento u otra respuesta
                    logger.debug(f"Mensaje recibido (no es nuestra respuesta): {response}")
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout esperando respuesta para {resource}.{action}")
            return None
            
        except Exception as e:
            logger.error(f"Error al enviar/recibir: {str(e)}")
            return None
    
    async def listen_for_events(self, duration=5):
        """Escucha eventos durante un tiempo determinado."""
        if not self.connected:
            logger.error("No conectado al servidor")
            return []
        
        events = []
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration:
                try:
                    # Esperar mensaje con timeout corto
                    message_raw = await asyncio.wait_for(
                        self.connection.recv(),
                        timeout=1
                    )
                    message = json.loads(message_raw)
                    
                    # Si es un evento, guardarlo
                    if message.get("type") == "event":
                        logger.info(f"Evento recibido: {message}")
                        events.append(message)
                    else:
                        logger.debug(f"Mensaje no-evento recibido: {message}")
                
                except asyncio.TimeoutError:
                    # Timeout esperado, continuar escuchando
                    pass
        
        except Exception as e:
            logger.error(f"Error al escuchar eventos: {str(e)}")
        
        return events
    
    def add_test_result(self, test_name, success, message="", data=None):
        """Añade un resultado de prueba."""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def run_tests(self):
        """Ejecuta todas las pruebas."""
        logger.info("Iniciando pruebas de WebSocket remoto")
        
        # Conectar al servidor
        connection_success = await self.connect()
        self.add_test_result("connection", connection_success, 
                            "Conexión exitosa" if connection_success else "Fallo de conexión")
        
        if not connection_success:
            logger.error("No se pudo conectar al servidor, abortando pruebas")
            return
        
        try:
            # Ejecutar pruebas
            await self.test_conversations()
            await self.test_messages()
            await self.test_users()
            await self.test_real_time_events()
            
        finally:
            # Desconectar al finalizar
            await self.disconnect()
        
        # Imprimir reporte
        self.print_report()
    
    async def test_conversations(self):
        """Prueba operaciones de conversaciones."""
        logger.info("Probando operaciones de conversaciones")
        
        # Prueba 1: Obtener todas las conversaciones
        response = await self.send_request("conversations", "get_all", {
            "user_id": self.test_user_id
        })
        
        if response and response.get("type") == "response":
            self.add_test_result("conversations.get_all", True, 
                                "Obtenidas conversaciones correctamente", 
                                response.get("payload"))
            
            # Si hay conversaciones, usar la primera para pruebas
            conversations = response.get("payload", {}).get("conversations", [])
            if conversations:
                self.test_conversation_id = conversations[0].get("id")
                logger.info(f"Usando conversación existente: {self.test_conversation_id}")
        else:
            self.add_test_result("conversations.get_all", False, 
                                "Error al obtener conversaciones", 
                                response)
        
        # Prueba 2: Crear una nueva conversación
        conversation_title = f"Test Conversation {datetime.now().isoformat()}"
        response = await self.send_request("conversations", "create", {
            "conversation": {
                "title": conversation_title,
                "created_by": self.test_user_id
            }
        })
        
        if response and response.get("type") == "response" and "conversation" in response.get("payload", {}):
            self.test_conversation_id = response["payload"]["conversation"]["id"]
            self.add_test_result("conversations.create", True, 
                                f"Conversación creada: {self.test_conversation_id}", 
                                response.get("payload"))
            logger.info(f"Conversación creada: {self.test_conversation_id}")
        else:
            self.add_test_result("conversations.create", False, 
                                "Error al crear conversación", 
                                response)
        
        # Prueba 3: Obtener una conversación específica
        if self.test_conversation_id:
            response = await self.send_request("conversations", "get", {
                "conversation_id": self.test_conversation_id
            })
            
            if response and response.get("type") == "response" and "conversation" in response.get("payload", {}):
                self.add_test_result("conversations.get", True, 
                                    f"Obtenida conversación: {self.test_conversation_id}", 
                                    response.get("payload"))
            else:
                self.add_test_result("conversations.get", False, 
                                    f"Error al obtener conversación: {self.test_conversation_id}", 
                                    response)
    
    async def test_messages(self):
        """Prueba operaciones de mensajes."""
        logger.info("Probando operaciones de mensajes")
        
        if not self.test_conversation_id:
            logger.warning("No hay conversación de prueba disponible, saltando pruebas de mensajes")
            self.add_test_result("messages", False, "No hay conversación de prueba disponible")
            return
        
        # Prueba 1: Obtener mensajes de una conversación
        response = await self.send_request("messages", "get_by_conversation", {
            "conversation_id": self.test_conversation_id
        })
        
        if response and response.get("type") == "response":
            self.add_test_result("messages.get_by_conversation", True, 
                                "Obtenidos mensajes correctamente", 
                                response.get("payload"))
            
            # Si hay mensajes, usar el primero para pruebas
            messages = response.get("payload", {}).get("messages", [])
            if messages:
                self.test_message_id = messages[0].get("id")
                logger.info(f"Usando mensaje existente: {self.test_message_id}")
        else:
            self.add_test_result("messages.get_by_conversation", False, 
                                "Error al obtener mensajes", 
                                response)
        
        # Prueba 2: Crear un nuevo mensaje
        message_content = f"Test Message {datetime.now().isoformat()}"
        response = await self.send_request("messages", "create", {
            "message": {
                "conversation_id": self.test_conversation_id,
                "content": message_content,
                "sender_id": self.test_user_id
            }
        })
        
        if response and response.get("type") == "response" and "message" in response.get("payload", {}):
            self.test_message_id = response["payload"]["message"]["id"]
            self.add_test_result("messages.create", True, 
                                f"Mensaje creado: {self.test_message_id}", 
                                response.get("payload"))
            logger.info(f"Mensaje creado: {self.test_message_id}")
        else:
            self.add_test_result("messages.create", False, 
                                "Error al crear mensaje", 
                                response)
        
        # Prueba 3: Obtener un mensaje específico
        if self.test_message_id:
            response = await self.send_request("messages", "get", {
                "message_id": self.test_message_id
            })
            
            if response and response.get("type") == "response" and "message" in response.get("payload", {}):
                self.add_test_result("messages.get", True, 
                                    f"Obtenido mensaje: {self.test_message_id}", 
                                    response.get("payload"))
            else:
                self.add_test_result("messages.get", False, 
                                    f"Error al obtener mensaje: {self.test_message_id}", 
                                    response)
    
    async def test_users(self):
        """Prueba operaciones de usuarios."""
        logger.info("Probando operaciones de usuarios")
        
        # Prueba 1: Obtener todos los usuarios
        response = await self.send_request("users", "get_all", {})
        
        if response and response.get("type") == "response":
            self.add_test_result("users.get_all", True, 
                                "Obtenidos usuarios correctamente", 
                                response.get("payload"))
        else:
            self.add_test_result("users.get_all", False, 
                                "Error al obtener usuarios", 
                                response)
        
        # Prueba 2: Obtener un usuario específico
        response = await self.send_request("users", "get", {
            "user_id": self.test_user_id
        })
        
        # No importa si el usuario existe o no, solo verificamos que la API responda
        if response:
            self.add_test_result("users.get", True, 
                                f"Solicitud de usuario procesada: {self.test_user_id}", 
                                response)
        else:
            self.add_test_result("users.get", False, 
                                f"Error al solicitar usuario: {self.test_user_id}", 
                                None)
    
    async def test_real_time_events(self):
        """Prueba eventos en tiempo real."""
        logger.info("Probando eventos en tiempo real")
        
        if not self.test_conversation_id:
            logger.warning("No hay conversación de prueba disponible, saltando pruebas de eventos")
            self.add_test_result("real_time_events", False, "No hay conversación de prueba disponible")
            return
        
        # Crear un mensaje para generar un evento
        message_content = f"Event Test Message {datetime.now().isoformat()}"
        await self.send_request("messages", "create", {
            "message": {
                "conversation_id": self.test_conversation_id,
                "content": message_content,
                "sender_id": self.test_user_id
            }
        })
        
        # Escuchar eventos durante 5 segundos
        logger.info("Escuchando eventos durante 5 segundos...")
        events = await self.listen_for_events(5)
        
        # Verificar si recibimos eventos
        if events:
            self.add_test_result("real_time_events", True, 
                                f"Recibidos {len(events)} eventos", 
                                events)
            logger.info(f"Recibidos {len(events)} eventos")
        else:
            self.add_test_result("real_time_events", False, 
                                "No se recibieron eventos", 
                                None)
            logger.warning("No se recibieron eventos")
    
    def print_report(self):
        """Imprime un reporte de las pruebas."""
        print("\n" + "="*80)
        print(f"REPORTE DE PRUEBAS WEBSOCKET - {self.base_url}")
        print("="*80)
        
        # Contar resultados
        total = len(self.test_results)
        successful = sum(1 for result in self.test_results if result["success"])
        failed = total - successful
        
        print(f"\nResumen: {successful}/{total} pruebas exitosas ({failed} fallidas)")
        print("-"*80)
        
        # Imprimir resultados detallados
        for i, result in enumerate(self.test_results, 1):
            status = "✅ ÉXITO" if result["success"] else "❌ FALLO"
            print(f"\n{i}. {result['test']} - {status}")
            print(f"   Mensaje: {result['message']}")
            
            # Imprimir datos si hay y no son muy largos
            if result["data"] and isinstance(result["data"], dict):
                # Limitar la salida para no saturar la consola
                data_str = json.dumps(result["data"], indent=2)
                if len(data_str) > 500:
                    data_str = data_str[:500] + "... [truncado]"
                print(f"   Datos: {data_str}")
        
        print("\n" + "="*80)
        
        # Recomendaciones basadas en resultados
        if failed > 0:
            print("\nRecomendaciones:")
            
            connection_failed = any(r["test"] == "connection" and not r["success"] for r in self.test_results)
            if connection_failed:
                print("- Verifica que el servidor WebSocket esté en ejecución y accesible")
                print("- Comprueba la URL y el protocolo (ws:// o wss://)")
                print("- Verifica si se requiere autenticación")
            
            if any(r["test"].startswith("conversations") and not r["success"] for r in self.test_results):
                print("- Revisa la implementación del handler de conversaciones")
            
            if any(r["test"].startswith("messages") and not r["success"] for r in self.test_results):
                print("- Revisa la implementación del handler de mensajes")
            
            if any(r["test"].startswith("users") and not r["success"] for r in self.test_results):
                print("- Revisa la implementación del handler de usuarios")
            
            if any(r["test"] == "real_time_events" and not r["success"] for r in self.test_results):
                print("- Verifica la implementación del sistema de eventos")
                print("- Comprueba que los eventos se estén disparando correctamente")
        
        print("\n" + "="*80)

async def main():
    """Función principal."""
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description="Prueba de WebSocket remoto")
    parser.add_argument("--url", default="waagentv1.onrender.com", help="URL base del servidor (sin protocolo)")
    parser.add_argument("--token", default=WEBSOCKET_AUTH_TOKEN, help="Token de autenticación (opcional, por defecto usa WEBSOCKET_AUTH_TOKEN)")
    parser.add_argument("--insecure", action="store_true", help="Usar conexión no segura (ws:// en lugar de wss://)")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout en segundos para operaciones")
    parser.add_argument("--debug", action="store_true", help="Activar modo debug")
    
    args = parser.parse_args()
    
    # Configurar nivel de logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Crear tester
    secure = not args.insecure
    tester = RemoteWebSocketTester(
        base_url=args.url,
        token=args.token,
        secure=secure,
        timeout=args.timeout
    )
    
    # Ejecutar pruebas
    await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main())
