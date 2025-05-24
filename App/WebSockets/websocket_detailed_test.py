#!/usr/bin/env python3
"""
Script ultra-detallado para capturar TODA la comunicación WebSocket
URL: wss://waagentv1.onrender.com/ws

Este script registra cada byte enviado y recibido para debug completo
"""

import asyncio
import websockets
import json
import logging
import time
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import traceback
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging MUY detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class DetailedWebSocketTester:
    def __init__(self):
        self.base_url = "wss://waagentv1.onrender.com"
        self.token = os.getenv("WEBSOCKET_AUTH_TOKEN")
        self.websocket = None
        self.connected = False
        self.client_id = None
        self.user_id = None
        
        # Contadores de comunicación
        self.messages_sent = 0
        self.messages_received = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        
        # Almacenar todos los mensajes para análisis
        self.communication_log = []
        
        # IDs de mensajes pendientes
        self.pending_requests = {}
        
    def log_communication(self, direction: str, message_type: str, data: Any, raw_data: str = None):
        """Registra cada comunicación en detalle"""
        timestamp = datetime.now()
        
        entry = {
            "timestamp": timestamp.isoformat(),
            "direction": direction,  # "SENT" o "RECEIVED"
            "message_type": message_type,
            "data": data,
            "raw_data": raw_data,
            "size_bytes": len(str(raw_data)) if raw_data else len(str(data))
        }
        
        self.communication_log.append(entry)
        
        # Log detallado
        size = entry["size_bytes"]
        logger.info(f"🔄 {direction} [{message_type}] ({size} bytes)")
        logger.info(f"📝 Raw: {raw_data}")
        logger.info(f"📊 Parsed: {json.dumps(data, indent=2) if isinstance(data, dict) else data}")
        logger.info("─" * 80)
    
    async def connect_with_details(self):
        """Conecta con logging ultra-detallado"""
        url = f"{self.base_url}/ws"
        if self.token:
            url += f"?token={self.token}"
        
        logger.info("🚀 INICIANDO CONEXIÓN WEBSOCKET DETALLADA")
        logger.info(f"📍 URL: {url}")
        logger.info(f"🔐 Token (primeros 20 chars): {self.token[:20] if self.token else 'None'}...")
        logger.info("=" * 80)
        
        try:
            # Conectar con timeout
            logger.info("🔌 Estableciendo conexión...")
            self.websocket = await asyncio.wait_for(
                websockets.connect(
                    url,
                    ping_interval=20,  # Ping cada 20 segundos
                    ping_timeout=10,   # Timeout de ping 10 segundos
                    close_timeout=10   # Timeout de cierre 10 segundos
                ),
                timeout=15.0
            )
            
            self.connected = True
            logger.info("✅ Conexión WebSocket establecida exitosamente")
            
            # Esperar mensaje de bienvenida
            logger.info("⏳ Esperando mensaje de bienvenida del servidor...")
            
            try:
                welcome_message = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
                self.log_communication("RECEIVED", "WELCOME", json.loads(welcome_message), welcome_message)
                
                # Parsear mensaje de bienvenida
                welcome_data = json.loads(welcome_message)
                if welcome_data.get("type") == "connected":
                    self.client_id = welcome_data.get("payload", {}).get("client_id")
                    self.user_id = welcome_data.get("payload", {}).get("user_id")
                    logger.info(f"🎯 Cliente ID asignado: {self.client_id}")
                    logger.info(f"👤 Usuario ID: {self.user_id}")
                
                self.messages_received += 1
                self.bytes_received += len(welcome_message)
                
            except asyncio.TimeoutError:
                logger.warning("⚠️ No se recibió mensaje de bienvenida en 10 segundos")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error al conectar: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    async def send_message_detailed(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Envía un mensaje con logging detallado y espera respuesta"""
        if not self.connected:
            logger.error("❌ No hay conexión WebSocket activa")
            return None
        
        # Generar ID si no existe
        if "id" not in message:
            message["id"] = str(uuid.uuid4())
        
        message_id = message["id"]
        
        try:
            # Serializar mensaje
            raw_message = json.dumps(message)
            
            # Log del envío
            self.log_communication("SENT", message.get("type", "unknown"), message, raw_message)
            
            # Enviar mensaje
            await self.websocket.send(raw_message)
            
            # Actualizar contadores
            self.messages_sent += 1
            self.bytes_sent += len(raw_message)
            
            logger.info(f"📤 Mensaje enviado exitosamente (ID: {message_id})")
            
            # Esperar respuesta específica para este mensaje
            logger.info(f"⏳ Esperando respuesta para mensaje {message_id}...")
            
            timeout = 15.0  # 15 segundos timeout
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    response_raw = await asyncio.wait_for(self.websocket.recv(), timeout=2.0)
                    response = json.loads(response_raw)
                    
                    # Log de la respuesta
                    self.log_communication("RECEIVED", response.get("type", "unknown"), response, response_raw)
                    
                    # Actualizar contadores
                    self.messages_received += 1
                    self.bytes_received += len(response_raw)
                    
                    # Verificar si es la respuesta que esperamos
                    if response.get("id") == message_id:
                        logger.info(f"✅ Respuesta recibida para mensaje {message_id}")
                        return response
                    else:
                        # Es otro tipo de mensaje (evento, heartbeat, etc.)
                        logger.info(f"📨 Mensaje adicional recibido: {response.get('type')} (ID: {response.get('id')})")
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"❌ Error al recibir mensaje: {str(e)}")
                    break
            
            logger.warning(f"⏰ Timeout esperando respuesta para mensaje {message_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error al enviar mensaje: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    async def test_basic_operations(self):
        """Prueba operaciones básicas con logging detallado"""
        logger.info("\n" + "🧪" + "="*60)
        logger.info("INICIANDO PRUEBAS DE OPERACIONES BÁSICAS")
        logger.info("="*61)
        
        operations = [
            # 1. Obtener todos los usuarios
            {
                "name": "Obtener todos los usuarios",
                "message": {
                    "type": "request",
                    "resource": "users",
                    "payload": {
                        "action": "get_all"
                    }
                }
            },
            
            # 2. Crear un usuario de prueba
            {
                "name": "Crear usuario de prueba",
                "message": {
                    "type": "request",
                    "resource": "users",
                    "payload": {
                        "action": "create",
                        "user": {
                            "phone": f"+57315{int(time.time() % 10000):04d}",
                            "email": f"test_{int(time.time())}@example.com",
                            "full_name": "Usuario de Prueba WebSocket",
                            "company": "Empresa de Prueba"
                        }
                    }
                }
            },
            
            # 3. Obtener conversaciones
            {
                "name": "Obtener conversaciones",
                "message": {
                    "type": "request",
                    "resource": "conversations",
                    "payload": {
                        "action": "get_all",
                        "user_id": "db0f337e-9802-4ea2-b29d-321851472d6d"  # Del health check
                    }
                }
            },
            
            # 4. Obtener mensajes de una conversación
            {
                "name": "Obtener mensajes de conversación",
                "message": {
                    "type": "request",
                    "resource": "messages",
                    "payload": {
                        "action": "get_by_conversation",
                        "conversation_id": "6efc1629-b598-448e-90ef-ecdc90323f45"  # Del health check
                    }
                }
            },
            
            # 5. Crear un mensaje de prueba
            {
                "name": "Crear mensaje de prueba",
                "message": {
                    "type": "request",
                    "resource": "messages",
                    "payload": {
                        "action": "create",
                        "message": {
                            "conversation_id": "6efc1629-b598-448e-90ef-ecdc90323f45",
                            "role": "user",
                            "content": f"Mensaje de prueba WebSocket - {datetime.now().isoformat()}",
                            "message_type": "text"
                        }
                    }
                }
            },
            
            # 6. Probar operación inválida (para ver manejo de errores)
            {
                "name": "Probar operación inválida",
                "message": {
                    "type": "request",
                    "resource": "invalid_resource",
                    "payload": {
                        "action": "invalid_action"
                    }
                }
            }
        ]
        
        results = []
        
        for i, operation in enumerate(operations, 1):
            logger.info(f"\n🔸 OPERACIÓN {i}/{len(operations)}: {operation['name']}")
            logger.info("─" * 50)
            
            response = await self.send_message_detailed(operation["message"])
            
            result = {
                "operation": operation["name"],
                "success": response is not None,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
            
            if response:
                if response.get("type") == "error":
                    logger.warning(f"⚠️ Error en operación: {response.get('payload', {}).get('message', 'Error desconocido')}")
                    result["error"] = response.get("payload")
                else:
                    logger.info(f"✅ Operación exitosa: {operation['name']}")
                    result["data"] = response.get("payload")
            else:
                logger.error(f"❌ Operación falló: {operation['name']}")
            
            results.append(result)
            
            # Pausa breve entre operaciones
            await asyncio.sleep(1)
        
        return results
    
    async def test_heartbeat_and_events(self):
        """Prueba heartbeats y eventos en tiempo real"""
        logger.info("\n" + "💓" + "="*60)
        logger.info("INICIANDO PRUEBA DE HEARTBEATS Y EVENTOS")
        logger.info("="*61)
        
        logger.info("⏳ Esperando heartbeats y eventos durante 30 segundos...")
        
        events_received = []
        heartbeats_received = []
        
        start_time = time.time()
        
        try:
            while time.time() - start_time < 30:  # 30 segundos
                try:
                    message_raw = await asyncio.wait_for(self.websocket.recv(), timeout=2.0)
                    message = json.loads(message_raw)
                    
                    # Log del mensaje
                    self.log_communication("RECEIVED", message.get("type", "unknown"), message, message_raw)
                    
                    # Clasificar mensaje
                    msg_type = message.get("type")
                    
                    if msg_type == "heartbeat":
                        heartbeats_received.append(message)
                        logger.info(f"💓 Heartbeat recibido: {message.get('payload', {}).get('timestamp')}")
                    elif msg_type == "event":
                        events_received.append(message)
                        event_type = message.get("payload", {}).get("type")
                        logger.info(f"🎉 Evento recibido: {event_type}")
                    else:
                        logger.info(f"📨 Mensaje recibido: {msg_type}")
                    
                    # Actualizar contadores
                    self.messages_received += 1
                    self.bytes_received += len(message_raw)
                    
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"❌ Error al recibir mensaje: {str(e)}")
                    break
        
        except Exception as e:
            logger.error(f"❌ Error durante prueba de eventos: {str(e)}")
        
        logger.info(f"📊 Resultados de 30 segundos:")
        logger.info(f"   💓 Heartbeats recibidos: {len(heartbeats_received)}")
        logger.info(f"   🎉 Eventos recibidos: {len(events_received)}")
        
        return {
            "heartbeats": heartbeats_received,
            "events": events_received
        }
    
    async def disconnect_detailed(self):
        """Desconecta con logging detallado"""
        if self.websocket and self.connected:
            logger.info("🔌 Cerrando conexión WebSocket...")
            try:
                await self.websocket.close()
                self.connected = False
                logger.info("✅ Conexión cerrada exitosamente")
            except Exception as e:
                logger.error(f"❌ Error al cerrar conexión: {str(e)}")
    
    def generate_communication_report(self):
        """Genera reporte detallado de toda la comunicación"""
        logger.info("\n" + "📊" + "="*60)
        logger.info("REPORTE DETALLADO DE COMUNICACIÓN WEBSOCKET")
        logger.info("="*61)
        
        # Estadísticas generales
        total_messages = len(self.communication_log)
        sent_messages = len([msg for msg in self.communication_log if msg["direction"] == "SENT"])
        received_messages = len([msg for msg in self.communication_log if msg["direction"] == "RECEIVED"])
        
        logger.info(f"📈 Estadísticas de comunicación:")
        logger.info(f"   📤 Mensajes enviados: {sent_messages}")
        logger.info(f"   📥 Mensajes recibidos: {received_messages}")
        logger.info(f"   📊 Total mensajes: {total_messages}")
        logger.info(f"   📦 Bytes enviados: {self.bytes_sent}")
        logger.info(f"   📦 Bytes recibidos: {self.bytes_received}")
        logger.info(f"   📦 Total bytes: {self.bytes_sent + self.bytes_received}")
        
        # Análisis por tipo de mensaje
        logger.info(f"\n📋 Mensajes por tipo:")
        message_types = {}
        for msg in self.communication_log:
            msg_type = msg["message_type"]
            direction = msg["direction"]
            key = f"{direction}_{msg_type}"
            message_types[key] = message_types.get(key, 0) + 1
        
        for key, count in sorted(message_types.items()):
            logger.info(f"   {key}: {count}")
        
        # Timeline de comunicación
        logger.info(f"\n⏰ Timeline de comunicación:")
        for i, msg in enumerate(self.communication_log):
            timestamp = msg["timestamp"]
            direction = msg["direction"]
            msg_type = msg["message_type"]
            size = msg["size_bytes"]
            logger.info(f"   {i+1:2d}. {timestamp} - {direction} {msg_type} ({size}b)")
        
        # Detectar patrones
        logger.info(f"\n🔍 Análisis de patrones:")
        
        # Verificar si hay respuestas para todas las solicitudes
        sent_requests = [msg for msg in self.communication_log 
                        if msg["direction"] == "SENT" and msg["message_type"] == "request"]
        received_responses = [msg for msg in self.communication_log 
                             if msg["direction"] == "RECEIVED" and msg["message_type"] in ["response", "error"]]
        
        logger.info(f"   📤 Solicitudes enviadas: {len(sent_requests)}")
        logger.info(f"   📥 Respuestas recibidas: {len(received_responses)}")
        
        if len(sent_requests) == len(received_responses):
            logger.info("   ✅ Todas las solicitudes recibieron respuesta")
        else:
            logger.info("   ⚠️ Algunas solicitudes no recibieron respuesta")
        
        # Verificar heartbeats
        heartbeats = [msg for msg in self.communication_log 
                     if msg["message_type"] == "heartbeat"]
        logger.info(f"   💓 Heartbeats recibidos: {len(heartbeats)}")
        
        return {
            "total_messages": total_messages,
            "sent_messages": sent_messages,
            "received_messages": received_messages,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "message_types": message_types,
            "communication_log": self.communication_log,
            "patterns": {
                "requests_sent": len(sent_requests),
                "responses_received": len(received_responses),
                "heartbeats_received": len(heartbeats)
            }
        }
    
    async def run_complete_test(self):
        """Ejecuta la prueba completa con máximo detalle"""
        logger.info("🔬 INICIANDO PRUEBA ULTRA-DETALLADA DE WEBSOCKET")
        logger.info(f"📍 URL: {self.base_url}")
        logger.info(f"🔐 Token configurado: {'Sí' if self.token else 'No'}")
        logger.info(f"⏰ Inicio: {datetime.now().isoformat()}")
        logger.info("=" * 80)
        
        try:
            # 1. Conectar
            if not await self.connect_with_details():
                logger.error("❌ No se pudo establecer conexión")
                return None
            
            # 2. Probar operaciones básicas
            operations_results = await self.test_basic_operations()
            
            # 3. Probar heartbeats y eventos
            events_results = await self.test_heartbeat_and_events()
            
            # 4. Generar reporte
            communication_report = self.generate_communication_report()
            
            # 5. Desconectar
            await self.disconnect_detailed()
            
            logger.info(f"\n⏰ Finalización: {datetime.now().isoformat()}")
            logger.info("🏁 PRUEBA ULTRA-DETALLADA COMPLETADA")
            
            return {
                "connection_successful": True,
                "operations_results": operations_results,
                "events_results": events_results,
                "communication_report": communication_report
            }
            
        except Exception as e:
            logger.error(f"❌ Error durante la prueba: {str(e)}")
            logger.error(traceback.format_exc())
            
            await self.disconnect_detailed()
            
            return {
                "connection_successful": False,
                "error": str(e),
                "communication_report": self.generate_communication_report() if self.communication_log else None
            }

async def main():
    """Función principal"""
    tester = DetailedWebSocketTester()
    
    try:
        results = await tester.run_complete_test()
        
        if results and results.get("connection_successful"):
            logger.info("🎉 ¡PRUEBA EXITOSA! El WebSocket está funcionando correctamente.")
            sys.exit(0)
        else:
            logger.error("💥 PRUEBA FALLÓ. Revisar logs para detalles.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⛔ Prueba interrumpida por el usuario")
        await tester.disconnect_detailed()
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Error fatal: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # Verificar dependencias
    try:
        import websockets
    except ImportError:
        print("❌ Error: websockets no está instalado")
        print("📦 Instálalo con: pip install websockets")
        sys.exit(1)
    
    print("🔬 PRUEBA ULTRA-DETALLADA WEBSOCKET - WAAGENTV1")
    print("=" * 60)
    print("📍 URL: wss://waagentv1.onrender.com/ws")
    print("🎯 Este script captura TODA la comunicación WebSocket")
    print("📊 Logging nivel DEBUG - cada byte será registrado")
    print("⏱️  Tiempo estimado: 2-3 minutos")
    print("=" * 60)
    
    asyncio.run(main())
