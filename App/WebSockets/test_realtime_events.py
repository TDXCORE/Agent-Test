#!/usr/bin/env python3
"""
Script completo para probar el sistema de eventos en tiempo real.
Verifica que todos los eventos se disparen y lleguen correctamente al frontend.
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime
import uuid

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

class RealtimeEventTester:
    def __init__(self, uri="ws://localhost:8000/ws"):
        self.uri = uri
        self.websocket = None
        self.received_events = []
        self.pending_requests = {}
        
    async def connect(self):
        """Conecta al WebSocket."""
        try:
            self.websocket = await websockets.connect(self.uri)
            logger.info("✅ Conectado al WebSocket")
            
            # Recibir mensaje de bienvenida
            welcome_message = await self.websocket.recv()
            logger.info(f"📨 Mensaje de bienvenida: {welcome_message}")
            
            return True
        except Exception as e:
            logger.error(f"❌ Error al conectar: {e}")
            return False
    
    async def disconnect(self):
        """Desconecta del WebSocket."""
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 Desconectado del WebSocket")
    
    async def send_request(self, resource, action, data=None, timeout=10):
        """Envía una solicitud y espera la respuesta."""
        request_id = f"test-{uuid.uuid4().hex[:8]}"
        
        message = {
            "type": "request",
            "id": request_id,
            "resource": resource,
            "payload": {
                "action": action,
                **(data or {})
            }
        }
        
        logger.info(f"📤 Enviando solicitud: {resource}.{action}")
        logger.debug(f"   Datos: {json.dumps(message, indent=2)}")
        
        # Enviar mensaje
        await self.websocket.send(json.dumps(message))
        
        # Esperar respuesta
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            response_data = json.loads(response)
            
            logger.info(f"📥 Respuesta recibida: {resource}.{action}")
            logger.debug(f"   Respuesta: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            return response_data
        except asyncio.TimeoutError:
            logger.error(f"⏰ Timeout esperando respuesta para {resource}.{action}")
            return None
        except Exception as e:
            logger.error(f"❌ Error al recibir respuesta: {e}")
            return None
    
    async def listen_for_events(self, duration=5):
        """Escucha eventos durante un tiempo determinado."""
        logger.info(f"👂 Escuchando eventos por {duration} segundos...")
        
        start_time = asyncio.get_event_loop().time()
        events_received = []
        
        try:
            while (asyncio.get_event_loop().time() - start_time) < duration:
                try:
                    # Esperar mensaje con timeout corto
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    # Solo procesar eventos
                    if data.get("type") == "event":
                        event_type = data.get("payload", {}).get("type", "unknown")
                        logger.info(f"🔔 EVENTO RECIBIDO: {event_type}")
                        logger.debug(f"   Datos: {json.dumps(data, indent=2, ensure_ascii=False)}")
                        
                        events_received.append({
                            "type": event_type,
                            "data": data,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        self.received_events.append(data)
                    
                except asyncio.TimeoutError:
                    # Timeout normal, continuar escuchando
                    continue
                except Exception as e:
                    logger.error(f"❌ Error al recibir evento: {e}")
                    break
        
        except Exception as e:
            logger.error(f"❌ Error durante escucha de eventos: {e}")
        
        logger.info(f"📊 Total eventos recibidos: {len(events_received)}")
        for event in events_received:
            logger.info(f"   - {event['type']} a las {event['timestamp']}")
        
        return events_received
    
    async def test_message_sending(self):
        """Prueba el envío de mensajes y eventos asociados."""
        logger.info("\n" + "="*60)
        logger.info("🧪 PRUEBA: Envío de mensajes y eventos")
        logger.info("="*60)
        
        # Primero obtener una conversación existente
        conversations_response = await self.send_request(
            "conversations", 
            "get_user_conversations", 
            {"agent_enabled": True}
        )
        
        if not conversations_response or not conversations_response.get("payload", {}).get("conversations"):
            logger.error("❌ No se encontraron conversaciones para probar")
            return False
        
        conversation = conversations_response["payload"]["conversations"][0]
        conversation_id = conversation["id"]
        
        logger.info(f"📋 Usando conversación: {conversation_id}")
        
        # Enviar un mensaje de prueba
        test_message = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": f"Mensaje de prueba - {datetime.now().isoformat()}",
            "message_type": "text",
            "read": False
        }
        
        # Iniciar escucha de eventos en paralelo
        event_task = asyncio.create_task(self.listen_for_events(10))
        
        # Esperar un poco antes de enviar
        await asyncio.sleep(1)
        
        # Enviar mensaje
        message_response = await self.send_request(
            "messages",
            "send_message",
            {"message": test_message}
        )
        
        if message_response and message_response.get("type") == "response":
            logger.info("✅ Mensaje enviado exitosamente")
            
            # Esperar un poco más para eventos
            await asyncio.sleep(2)
            
            # Marcar mensajes como leídos
            read_response = await self.send_request(
                "messages",
                "mark_as_read",
                {"conversation_id": conversation_id}
            )
            
            if read_response:
                logger.info("✅ Mensajes marcados como leídos")
        else:
