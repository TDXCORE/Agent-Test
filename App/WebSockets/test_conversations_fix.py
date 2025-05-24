#!/usr/bin/env python3
"""
Script para probar la corrección del handler de conversaciones.
Verifica que los datos de usuario se incluyan correctamente en las conversaciones.
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)8s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

async def test_conversations_with_users():
    """Prueba que las conversaciones incluyan datos de usuario."""
    
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Conectado al WebSocket")
            
            # Recibir mensaje de bienvenida
            welcome_message = await websocket.recv()
            logger.info(f"📨 Mensaje de bienvenida: {welcome_message}")
            
            # Test 1: Obtener conversaciones con agente habilitado
            test_request = {
                "type": "request",
                "id": "test-conversations-with-users",
                "resource": "conversations",
                "payload": {
                    "action": "get_user_conversations",
                    "agent_enabled": True
                }
            }
            
            logger.info("🧪 Enviando solicitud para conversaciones con agente habilitado...")
            await websocket.send(json.dumps(test_request, indent=2))
            
            # Recibir respuesta
            response = await websocket.recv()
            response_data = json.loads(response)
            
            logger.info("📥 Respuesta recibida:")
            logger.info(json.dumps(response_data, indent=2, ensure_ascii=False))
            
            # Analizar la respuesta
            if response_data.get("type") == "response":
                conversations = response_data.get("payload", {}).get("conversations", [])
                logger.info(f"📊 Total conversaciones: {len(conversations)}")
                
                if conversations:
                    # Verificar la primera conversación
                    first_conv = conversations[0]
                    logger.info("🔍 Analizando primera conversación:")
                    
                    # Verificar si tiene datos de usuario
                    user_data = first_conv.get("user") or first_conv.get("users")
                    if user_data:
                        logger.info("✅ Datos de usuario encontrados:")
                        if isinstance(user_data, list):
                            user_data = user_data[0] if user_data else {}
                        logger.info(f"   - Nombre: {user_data.get('full_name', 'N/A')}")
                        logger.info(f"   - Email: {user_data.get('email', 'N/A')}")
                        logger.info(f"   - Teléfono: {user_data.get('phone', 'N/A')}")
                        logger.info(f"   - Empresa: {user_data.get('company', 'N/A')}")
                    else:
                        logger.warning("❌ No se encontraron datos de usuario en la conversación")
                        logger.info("📋 Campos disponibles en la conversación:")
                        for key in first_conv.keys():
                            logger.info(f"   - {key}: {type(first_conv[key])}")
                    
                    # Verificar último mensaje
                    last_message = first_conv.get("last_message")
                    if last_message:
                        logger.info("✅ Último mensaje encontrado:")
                        logger.info(f"   - Contenido: {last_message.get('content', 'N/A')[:50]}...")
                        logger.info(f"   - Rol: {last_message.get('role', 'N/A')}")
                        logger.info(f"   - Fecha: {last_message.get('created_at', 'N/A')}")
                    
                    # Verificar contador de no leídos
                    unread_count = first_conv.get("unread_count", 0)
                    logger.info(f"📬 Mensajes no leídos: {unread_count}")
                    
                else:
                    logger.info("ℹ️ No se encontraron conversaciones con agente habilitado")
            
            # Test 2: Obtener conversaciones con agente deshabilitado
            test_request_disabled = {
                "type": "request",
                "id": "test-conversations-disabled",
                "resource": "conversations",
                "payload": {
                    "action": "get_user_conversations",
                    "agent_enabled": False
                }
            }
            
            logger.info("\n🧪 Enviando solicitud para conversaciones con agente deshabilitado...")
            await websocket.send(json.dumps(test_request_disabled, indent=2))
            
            # Recibir respuesta
            response_disabled = await websocket.recv()
            response_disabled_data = json.loads(response_disabled)
            
            conversations_disabled = response_disabled_data.get("payload", {}).get("conversations", [])
            logger.info(f"📊 Total conversaciones con agente deshabilitado: {len(conversations_disabled)}")
            
            logger.info("✅ Prueba completada exitosamente")
            
    except ConnectionRefusedError:
        logger.error("❌ No se pudo conectar al WebSocket. ¿Está el servidor ejecutándose?")
        logger.info("💡 Para iniciar el servidor: python -m App.WebSockets.main")
    except Exception as e:
        logger.error(f"❌ Error durante la prueba: {str(e)}")
        import traceback
        logger.error(f"Traza completa: {traceback.format_exc()}")

async def test_conversation_details():
    """Prueba obtener detalles de una conversación específica."""
    
    uri = "ws://localhost:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("✅ Conectado al WebSocket para prueba de detalles")
            
            # Recibir mensaje de bienvenida
            await websocket.recv()
            
            # Primero obtener una lista de conversaciones para tener un ID válido
            list_request = {
                "type": "request",
                "id": "get-conversation-list",
                "resource": "conversations",
                "payload": {
                    "action": "get_user_conversations",
                    "agent_enabled": True
                }
            }
            
            await websocket.send(json.dumps(list_request))
            list_response = await websocket.recv()
            list_data = json.loads(list_response)
            
            conversations = list_data.get("payload", {}).get("conversations", [])
            
            if conversations:
                conversation_id = conversations[0]["id"]
                logger.info(f"🔍 Probando detalles para conversación: {conversation_id}")
                
                # Solicitar detalles de la conversación
                details_request = {
                    "type": "request",
                    "id": "get-conversation-details",
                    "resource": "conversations",
                    "payload": {
                        "action": "get_conversation_with_details",
                        "conversation_id": conversation_id
                    }
                }
                
                await websocket.send(json.dumps(details_request))
                details_response = await websocket.recv()
                details_data = json.loads(details_response)
                
                logger.info("📋 Detalles de conversación:")
                logger.info(json.dumps(details_data, indent=2, ensure_ascii=False))
                
            else:
                logger.info("ℹ️ No hay conversaciones disponibles para probar detalles")
                
    except Exception as e:
        logger.error(f"❌ Error en prueba de detalles: {str(e)}")

async def main():
    """Función principal que ejecuta todas las pruebas."""
    logger.info("🚀 Iniciando pruebas de corrección de conversaciones")
    logger.info("=" * 60)
    
    # Prueba 1: Conversaciones con datos de usuario
    logger.info("📋 PRUEBA 1: Conversaciones con datos de usuario")
    await test_conversations_with_users()
    
    logger.info("\n" + "=" * 60)
    
    # Prueba 2: Detalles de conversación
    logger.info("📋 PRUEBA 2: Detalles de conversación específica")
    await test_conversation_details()
    
    logger.info("\n" + "=" * 60)
    logger.info("🏁 Todas las pruebas completadas")

if __name__ == "__main__":
    asyncio.run(main())
