"""
🔍 SCRIPT DE DIAGNÓSTICO ESPECÍFICO PARA HANDLERS
===============================================
Diagnóstica problemas específicos en cada handler para identificar
la causa de los timeouts y errores.
"""

import asyncio
import websockets
import json
import uuid
import time
from datetime import datetime

WEBSOCKET_URL = "ws://localhost:8000/ws"

async def test_single_handler(handler_name, action_name, payload=None):
    """Prueba una sola función de handler con logging detallado."""
    print(f"\n🔍 TESTING: {handler_name}.{action_name}")
    
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            # Recibir mensaje de bienvenida
            welcome = await websocket.recv()
            print(f"✅ Conectado, bienvenida recibida")
            
            # Preparar mensaje
            message = {
                "type": "request",
                "id": str(uuid.uuid4()),
                "resource": handler_name,
                "payload": {"action": action_name}
            }
            
            if payload:
                message["payload"].update(payload)
            
            print(f"📤 Enviando: {json.dumps(message, indent=2)}")
            
            # Enviar mensaje
            start_time = time.time()
            await websocket.send(json.dumps(message))
            
            # Recibir respuesta con timeout corto
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                end_time = time.time()
                
                response_data = json.loads(response)
                print(f"📥 Respuesta ({(end_time-start_time)*1000:.1f}ms): {json.dumps(response_data, indent=2)}")
                
                if response_data.get("type") == "error":
                    print(f"❌ ERROR: {response_data.get('payload', {}).get('message', 'Error desconocido')}")
                else:
                    print(f"✅ ÉXITO")
                    
            except asyncio.TimeoutError:
                print(f"⏰ TIMEOUT después de 5 segundos")
                
    except Exception as e:
        print(f"💥 EXCEPCIÓN: {str(e)}")

async def test_all_handlers():
    """Prueba handlers uno por uno para identificar problemas."""
    
    print("🔍 DIAGNÓSTICO DETALLADO DE HANDLERS")
    print("=" * 50)
    
    # Crear un usuario real primero para las pruebas
    print("\n🏗️ CREANDO USUARIO DE PRUEBA...")
    await test_single_handler("users", "create_user", {
        "user": {
            "full_name": "Usuario Debug",
            "email": "debug@test.com",
            "phone": "+1234567890",
            "company": "Debug Corp"
        }
    })
    
    # Obtener usuarios para conseguir un ID real
    print("\n📋 OBTENIENDO USUARIOS EXISTENTES...")
    await test_single_handler("users", "get_all_users")
    
    # Probar cada handler con funciones básicas
    handlers_to_test = [
        ("users", "get_all_users"),
        ("conversations", "get_all_conversations", {"user_id": str(uuid.uuid4())}),
        ("messages", "get_all_messages"),
        ("dashboard", "get_dashboard_stats"),
        ("dashboard", "get_conversion_funnel"),
        ("leads", "get_all_leads"),
        ("leads", "get_lead_pipeline"),
        ("meetings", "get_all_meetings", {"filter": "today"}),
        ("requirements", "get_popular_features"),
        ("requirements", "get_popular_integrations")
    ]
    
    for test_data in handlers_to_test:
        handler = test_data[0]
        action = test_data[1]
        payload = test_data[2] if len(test_data) > 2 else None
        
        await test_single_handler(handler, action, payload)
        
        # Pausa entre pruebas
        await asyncio.sleep(1)

async def test_specific_issues():
    """Prueba problemas específicos identificados."""
    
    print("\n\n🎯 PRUEBAS ESPECÍFICAS DE PROBLEMAS")
    print("=" * 50)
    
    # 1. Probar si el problema es con handlers específicos
    print("\n1️⃣ Probando handlers que funcionaban antes...")
    
    # Estos funcionaban en pruebas anteriores
    working_handlers = [
        ("dashboard", "get_conversion_funnel"),
        ("dashboard", "get_real_time_metrics"),
        ("leads", "update_lead_step", {"lead_id": str(uuid.uuid4()), "new_step": "requirements"}),
        ("meetings", "sync_outlook_calendar"),
        ("requirements", "get_popular_integrations")
    ]
    
    for test_data in working_handlers:
        handler = test_data[0]
        action = test_data[1]
        payload = test_data[2] if len(test_data) > 2 else None
        
        await test_single_handler(handler, action, payload)
        await asyncio.sleep(0.5)

async def main():
    """Función principal."""
    try:
        await test_all_handlers()
        await test_specific_issues()
        
    except KeyboardInterrupt:
        print("\n⏹️ Diagnóstico interrumpido")
    except Exception as e:
        print(f"\n💥 Error en diagnóstico: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
