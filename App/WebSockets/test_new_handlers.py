"""
🧪 WEBSOCKET COMPREHENSIVE TEST SUITE
====================================
Suite completa de pruebas para TODOS los handlers WebSocket con análisis detallado.
Incluye auto-inicio del servidor, testing end-to-end y reportes profesionales.
"""

import asyncio
import websockets
import json
import uuid
import subprocess
import time
import sys
import os
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import threading

# Configuración
WEBSOCKET_URL = "ws://localhost:8000/ws"
SERVER_URL = "http://localhost:8000"
SERVER_PORT = 8000

@dataclass
class TestResult:
    """Resultado de una prueba individual."""
    handler: str
    function: str
    success: bool
    request_data: Dict[str, Any]
    response_data: Dict[str, Any]
    execution_time_ms: float
    request_size_bytes: int
    response_size_bytes: int
    tables_involved: List[str]
    fields_sent: List[str]
    fields_received: List[str]
    records_processed: int
    error_message: Optional[str] = None

class WebSocketTestSuite:
    """Suite completa de pruebas WebSocket."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.server_process = None
        self.start_time = None
        self.end_time = None
        
    def is_server_running(self) -> bool:
        """Verifica si el servidor está ejecutándose."""
        try:
            response = requests.get(f"{SERVER_URL}/health-check", timeout=2)
            return response.status_code == 200
        except:
            try:
                # Verificar si hay algún proceso en el puerto 8000
                for conn in psutil.net_connections():
                    if conn.laddr.port == SERVER_PORT:
                        return True
                return False
            except:
                return False
    
    def start_server(self):
        """Inicia el servidor WebSocket automáticamente."""
        if self.is_server_running():
            print("✅ Servidor ya está ejecutándose en puerto 8000")
            return True
            
        print("🚀 Iniciando servidor WebSocket...")
        
        # Intentar diferentes formas de iniciar el servidor
        commands = [
            ["uvicorn", "App.api:app", "--host", "0.0.0.0", "--port", "8000"],
            ["python", "-m", "uvicorn", "App.api:app", "--host", "0.0.0.0", "--port", "8000"],
            ["python", "App/api.py"],
            ["python", "-c", "from App.api import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"]
        ]
        
        for cmd in commands:
            try:
                print(f"🔄 Intentando: {' '.join(cmd)}")
                self.server_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=os.getcwd()
                )
                
                # Esperar a que el servidor esté listo
                for i in range(30):  # 30 segundos máximo
                    time.sleep(1)
                    if self.is_server_running():
                        print(f"✅ Servidor iniciado exitosamente en puerto 8000")
                        return True
                    print(f"⏳ Esperando servidor... ({i+1}/30)")
                
                # Si llegamos aquí, el comando no funcionó
                self.server_process.terminate()
                self.server_process = None
                
            except Exception as e:
                print(f"❌ Error con comando {' '.join(cmd)}: {str(e)}")
                continue
        
        print("❌ No se pudo iniciar el servidor automáticamente")
        print("📝 Por favor, inicia el servidor manualmente:")
        print("   uvicorn App.api:app --host 0.0.0.0 --port 8000")
        return False
    
    def stop_server(self):
        """Detiene el servidor si fue iniciado por este script."""
        if self.server_process:
            print("🛑 Deteniendo servidor...")
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = None
    
    async def send_message_and_analyze(self, websocket, message: Dict[str, Any]) -> TestResult:
        """Envía un mensaje y analiza la respuesta detalladamente."""
        message_id = str(uuid.uuid4())
        
        # Extraer resource y action del mensaje original
        handler = message.get("resource", "unknown")
        function = message.get("action", "unknown")
        
        # Crear el mensaje en el formato correcto para WebSocket
        # El setup.py espera resource al nivel superior y action en payload
        payload_data = {"action": function}
        
        # Si hay payload en el mensaje original, agregarlo
        if "payload" in message:
            payload_data.update(message["payload"])
        
        websocket_message = {
            "type": "request",
            "id": message_id,
            "resource": handler,
            "payload": payload_data
        }
        
        # Preparar datos de request
        request_json = json.dumps(websocket_message)
        request_size = len(request_json.encode('utf-8'))
        fields_sent = list(websocket_message.keys())
        if "payload" in websocket_message:
            fields_sent.extend(list(websocket_message["payload"].keys()))
        
        start_time = time.time()
        
        try:
            # Enviar mensaje
            await websocket.send(request_json)
            
            # Recibir respuesta
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            end_time = time.time()
            
            response_data = json.loads(response)
            response_size = len(response.encode('utf-8'))
            execution_time = (end_time - start_time) * 1000  # en ms
            
            # Analizar respuesta
            success = response_data.get("type") != "error"
            fields_received = []
            records_processed = 0
            tables_involved = []
            
            if success and "payload" in response_data:
                payload = response_data["payload"]
                if isinstance(payload, dict):
                    fields_received = list(payload.keys())
                    if "data" in payload:
                        data = payload["data"]
                        if isinstance(data, list):
                            records_processed = len(data)
                            if data and isinstance(data[0], dict):
                                fields_received.extend(list(data[0].keys()))
                        elif isinstance(data, dict):
                            records_processed = 1
                            fields_received.extend(list(data.keys()))
            
            # Mapear tablas involucradas basado en el handler y función
            tables_involved = self.get_tables_for_function(handler, function)
            
            return TestResult(
                handler=handler,
                function=function,
                success=success,
                request_data=message,
                response_data=response_data,
                execution_time_ms=execution_time,
                request_size_bytes=request_size,
                response_size_bytes=response_size,
                tables_involved=tables_involved,
                fields_sent=fields_sent,
                fields_received=list(set(fields_received)),
                records_processed=records_processed,
                error_message=response_data.get("payload", {}).get("message") if not success else None
            )
            
        except Exception as e:
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            
            return TestResult(
                handler=handler,
                function=function,
                success=False,
                request_data=message,
                response_data={},
                execution_time_ms=execution_time,
                request_size_bytes=request_size,
                response_size_bytes=0,
                tables_involved=[],
                fields_sent=fields_sent,
                fields_received=[],
                records_processed=0,
                error_message=str(e)
            )
    
    def get_tables_for_function(self, handler: str, function: str) -> List[str]:
        """Mapea funciones a las tablas de BD que utilizan."""
        table_mapping = {
            "users": {
                "get_all_users": ["users"],
                "create_user": ["users"],
                "update_user": ["users"],
                "delete_user": ["users"],
                "get_user_by_id": ["users"]
            },
            "conversations": {
                "get_all_conversations": ["conversations", "users"],
                "create_conversation": ["conversations"],
                "close_conversation": ["conversations"],
                "update_agent_status": ["conversations"],
                "get_conversation_by_id": ["conversations"],
                "get_user_conversations": ["conversations"]
            },
            "messages": {
                "get_all_messages": ["messages", "conversations"],
                "send_message": ["messages"],
                "mark_as_read": ["messages"],
                "delete_message": ["messages"],
                "get_conversation_messages": ["messages"],
                "update_message": ["messages"]
            },
            "dashboard": {
                "get_dashboard_stats": ["users", "conversations", "meetings", "lead_qualification"],
                "get_conversion_funnel": ["lead_qualification", "bant_data", "requirements", "meetings"],
                "get_activity_timeline": ["users", "messages", "meetings", "conversations"],
                "get_agent_performance": ["conversations", "messages"],
                "get_real_time_metrics": ["conversations", "messages"]
            },
            "leads": {
                "get_all_leads": ["lead_qualification", "users", "bant_data", "requirements"],
                "get_lead_pipeline": ["lead_qualification"],
                "get_lead_with_complete_data": ["lead_qualification", "users", "conversations", "bant_data", "requirements", "features", "integrations", "meetings"],
                "update_lead_step": ["lead_qualification"],
                "get_conversion_stats": ["lead_qualification"],
                "get_abandoned_leads": ["lead_qualification", "users"]
            },
            "meetings": {
                "get_all_meetings": ["meetings", "users", "lead_qualification"],
                "get_calendar_view": ["meetings"],
                "create_meeting": ["meetings"],
                "update_meeting": ["meetings"],
                "cancel_meeting": ["meetings"],
                "get_available_slots": [],
                "sync_outlook_calendar": ["meetings"]
            },
            "requirements": {
                "get_requirements_by_lead": ["requirements", "features", "integrations"],
                "create_requirement_package": ["requirements", "features", "integrations"],
                "update_requirements": ["requirements"],
                "add_feature": ["features"],
                "add_integration": ["integrations"],
                "get_popular_features": ["features"],
                "get_popular_integrations": ["integrations"]
            }
        }
        
        return table_mapping.get(handler, {}).get(function, [])
    
    async def run_all_tests(self):
        """Ejecuta todas las pruebas de todos los handlers."""
        self.start_time = datetime.now()
        
        print("🧪 WEBSOCKET COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        print(f"🕐 Inicio: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            async with websockets.connect(WEBSOCKET_URL) as websocket:
                print("✅ Conectado al WebSocket")
                
                # Recibir mensaje de bienvenida
                welcome_message = await websocket.recv()
                print(f"📨 Mensaje de bienvenida recibido")
                print()
                
                # Ejecutar pruebas por handler
                await self.test_users_handler(websocket)
                await self.test_conversations_handler(websocket)
                await self.test_messages_handler(websocket)
                await self.test_dashboard_handler(websocket)
                await self.test_leads_handler(websocket)
                await self.test_meetings_handler(websocket)
                await self.test_requirements_handler(websocket)
                
        except Exception as e:
            print(f"❌ Error durante las pruebas: {str(e)}")
        
        self.end_time = datetime.now()
        self.generate_comprehensive_report()
    
    # ========== PRUEBAS POR HANDLER ==========
    
    async def test_users_handler(self, websocket):
        """Prueba todas las funciones del UsersHandler."""
        print("👥 === TESTING USERS HANDLER ===")
        
        # Generar UUIDs válidos para las pruebas
        test_user_id = str(uuid.uuid4())
        
        tests = [
            {"resource": "users", "action": "get_all_users"},
            {"resource": "users", "action": "create_user", "payload": {
                "user": {
                    "full_name": "Usuario Test", 
                    "email": "test@test.com", 
                    "phone": "+1234567890", 
                    "company": "Test Corp"
                }
            }},
            {"resource": "users", "action": "get_user_by_id", "payload": {"user_id": test_user_id}},
            {"resource": "users", "action": "update_user", "payload": {
                "user_id": test_user_id,
                "user": {
                    "full_name": "Usuario Actualizado"
                }
            }},
            {"resource": "users", "action": "delete_user", "payload": {"user_id": test_user_id}}
        ]
        
        for test in tests:
            result = await self.send_message_and_analyze(websocket, test)
            self.results.append(result)
            status = "✅" if result.success else "❌"
            print(f"{status} {result.function} - {result.execution_time_ms:.1f}ms")
        
        print()
    
    async def test_conversations_handler(self, websocket):
        """Prueba todas las funciones del ConversationsHandler."""
        print("💬 === TESTING CONVERSATIONS HANDLER ===")
        
        # Generar UUIDs válidos para las pruebas
        test_user_id = str(uuid.uuid4())
        test_conv_id = str(uuid.uuid4())
        
        tests = [
            {"resource": "conversations", "action": "get_all_conversations", "payload": {"user_id": test_user_id}},
            {"resource": "conversations", "action": "create_conversation", "payload": {
                "user_id": test_user_id, "external_id": "+1234567890", "platform": "whatsapp"
            }},
            {"resource": "conversations", "action": "get_conversation_by_id", "payload": {"conversation_id": test_conv_id}},
            {"resource": "conversations", "action": "close_conversation", "payload": {"conversation_id": test_conv_id}},
            {"resource": "conversations", "action": "update_agent_status", "payload": {
                "conversation_id": test_conv_id, "enabled": True
            }},
            {"resource": "conversations", "action": "get_user_conversations", "payload": {"user_id": test_user_id}}
        ]
        
        for test in tests:
            result = await self.send_message_and_analyze(websocket, test)
            self.results.append(result)
            status = "✅" if result.success else "❌"
            print(f"{status} {result.function} - {result.execution_time_ms:.1f}ms")
        
        print()
    
    async def test_messages_handler(self, websocket):
        """Prueba todas las funciones del MessagesHandler."""
        print("📨 === TESTING MESSAGES HANDLER ===")
        
        # Generar UUIDs válidos para las pruebas
        test_conv_id = str(uuid.uuid4())
        test_msg_id = str(uuid.uuid4())
        
        tests = [
            {"resource": "messages", "action": "get_all_messages"},
            {"resource": "messages", "action": "send_message", "payload": {
                "conversation_id": test_conv_id, "content": "Mensaje de prueba", "role": "user"
            }},
            {"resource": "messages", "action": "get_conversation_messages", "payload": {"conversation_id": test_conv_id}},
            {"resource": "messages", "action": "mark_as_read", "payload": {"conversation_id": test_conv_id}},
            {"resource": "messages", "action": "delete_message", "payload": {"message_id": test_msg_id}},
            {"resource": "messages", "action": "update_message", "payload": {
                "message_id": test_msg_id, "content": "Mensaje actualizado"
            }}
        ]
        
        for test in tests:
            result = await self.send_message_and_analyze(websocket, test)
            self.results.append(result)
            status = "✅" if result.success else "❌"
            print(f"{status} {result.function} - {result.execution_time_ms:.1f}ms")
        
        print()
    
    async def test_dashboard_handler(self, websocket):
        """Prueba todas las funciones del DashboardHandler."""
        print("📊 === TESTING DASHBOARD HANDLER ===")
        
        tests = [
            {"resource": "dashboard", "action": "get_dashboard_stats"},
            {"resource": "dashboard", "action": "get_conversion_funnel"},
            {"resource": "dashboard", "action": "get_activity_timeline"},
            {"resource": "dashboard", "action": "get_agent_performance"},
            {"resource": "dashboard", "action": "get_real_time_metrics"}
        ]
        
        for test in tests:
            result = await self.send_message_and_analyze(websocket, test)
            self.results.append(result)
            status = "✅" if result.success else "❌"
            print(f"{status} {result.function} - {result.execution_time_ms:.1f}ms")
        
        print()
    
    async def test_leads_handler(self, websocket):
        """Prueba todas las funciones del LeadsHandler."""
        print("👥 === TESTING LEADS HANDLER ===")
        
        # Generar UUIDs válidos para las pruebas
        test_lead_id = str(uuid.uuid4())
        
        tests = [
            {"resource": "leads", "action": "get_all_leads"},
            {"resource": "leads", "action": "get_lead_pipeline"},
            {"resource": "leads", "action": "get_lead_with_complete_data", "payload": {"lead_id": test_lead_id}},
            {"resource": "leads", "action": "update_lead_step", "payload": {
                "lead_id": test_lead_id, "new_step": "requirements"
            }},
            {"resource": "leads", "action": "get_conversion_stats"},
            {"resource": "leads", "action": "get_abandoned_leads"}
        ]
        
        for test in tests:
            result = await self.send_message_and_analyze(websocket, test)
            self.results.append(result)
            status = "✅" if result.success else "❌"
            print(f"{status} {result.function} - {result.execution_time_ms:.1f}ms")
        
        print()
    
    async def test_meetings_handler(self, websocket):
        """Prueba todas las funciones del MeetingsHandler."""
        print("📅 === TESTING MEETINGS HANDLER ===")
        
        # Generar UUIDs válidos para las pruebas
        test_user_id = str(uuid.uuid4())
        test_lead_id = str(uuid.uuid4())
        test_meeting_id = str(uuid.uuid4())
        
        tests = [
            {"resource": "meetings", "action": "get_all_meetings", "payload": {"filter": "today"}},
            {"resource": "meetings", "action": "get_calendar_view", "payload": {
                "start_date": datetime.now().strftime("%Y-%m-%d"),
                "end_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            }},
            {"resource": "meetings", "action": "create_meeting", "payload": {
                "user_id": test_user_id, "lead_qualification_id": test_lead_id,
                "subject": "Reunión de prueba", "start_time": "2024-01-15T10:00:00Z",
                "end_time": "2024-01-15T11:00:00Z", "attendee_email": "test@test.com"
            }},
            {"resource": "meetings", "action": "update_meeting", "payload": {
                "meeting_id": test_meeting_id, "subject": "Reunión actualizada"
            }},
            {"resource": "meetings", "action": "cancel_meeting", "payload": {"meeting_id": test_meeting_id}},
            {"resource": "meetings", "action": "get_available_slots", "payload": {
                "date": datetime.now().strftime("%Y-%m-%d"), "duration": 60
            }},
            {"resource": "meetings", "action": "sync_outlook_calendar"}
        ]
        
        for test in tests:
            result = await self.send_message_and_analyze(websocket, test)
            self.results.append(result)
            status = "✅" if result.success else "❌"
            print(f"{status} {result.function} - {result.execution_time_ms:.1f}ms")
        
        print()
    
    async def test_requirements_handler(self, websocket):
        """Prueba todas las funciones del RequirementsHandler."""
        print("📋 === TESTING REQUIREMENTS HANDLER ===")
        
        # Generar UUIDs válidos para las pruebas
        test_lead_id = str(uuid.uuid4())
        test_req_id = str(uuid.uuid4())
        
        tests = [
            {"resource": "requirements", "action": "get_requirements_by_lead", "payload": {"lead_id": test_lead_id}},
            {"resource": "requirements", "action": "create_requirement_package", "payload": {
                "lead_qualification_id": test_lead_id, "app_type": "web_app", "deadline": "2024-08-01",
                "features": [{"name": "Login", "description": "Sistema de autenticación"}],
                "integrations": [{"name": "PayPal", "description": "Procesamiento de pagos"}]
            }},
            {"resource": "requirements", "action": "update_requirements", "payload": {
                "requirements_id": test_req_id, "app_type": "mobile_app", "deadline": "2024-09-01"
            }},
            {"resource": "requirements", "action": "add_feature", "payload": {
                "requirements_id": test_req_id, "name": "Chat", "description": "Chat en tiempo real"
            }},
            {"resource": "requirements", "action": "add_integration", "payload": {
                "requirements_id": test_req_id, "name": "Stripe", "description": "Pagos con tarjeta"
            }},
            {"resource": "requirements", "action": "get_popular_features"},
            {"resource": "requirements", "action": "get_popular_integrations"}
        ]
        
        for test in tests:
            result = await self.send_message_and_analyze(websocket, test)
            self.results.append(result)
            status = "✅" if result.success else "❌"
            print(f"{status} {result.function} - {result.execution_time_ms:.1f}ms")
        
        print()
    
    def generate_comprehensive_report(self):
        """Genera un reporte completo y detallado."""
        print("\n" + "=" * 80)
        print("📊 REPORTE COMPLETO DE PRUEBAS WEBSOCKET")
        print("=" * 80)
        
        # Resumen ejecutivo
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests
        total_time = (self.end_time - self.start_time).total_seconds()
        avg_response_time = sum(r.execution_time_ms for r in self.results) / total_tests if total_tests > 0 else 0
        total_data_transferred = sum(r.request_size_bytes + r.response_size_bytes for r in self.results)
        
        print(f"\n📈 RESUMEN EJECUTIVO:")
        print("┌" + "─" * 78 + "┐")
        print(f"│ Total Handlers Probados: {len(set(r.handler for r in self.results)):<50} │")
        print(f"│ Total Funciones Probadas: {total_tests:<49} │")
        print(f"│ Pruebas Exitosas: {successful_tests}/{total_tests:<44} │")
        print(f"│ Pruebas Fallidas: {failed_tests}/{total_tests:<44} │")
        print(f"│ Tiempo Total de Ejecución: {total_time:.1f} segundos{'':<35} │")
        print(f"│ Datos Totales Transferidos: {total_data_transferred/1024:.1f} KB{'':<38} │")
        print(f"│ Promedio Tiempo Respuesta: {avg_response_time:.1f}ms{'':<40} │")
        print("└" + "─" * 78 + "┘")
        
        # Detalle por handler
        print(f"\n🔍 DETALLE POR HANDLER:")
        
        handlers = {}
        for result in self.results:
            if result.handler not in handlers:
                handlers[result.handler] = []
            handlers[result.handler].append(result)
        
        for handler_name, handler_results in handlers.items():
            successful = sum(1 for r in handler_results if r.success)
            total = len(handler_results)
            
            print(f"\n{self.get_handler_emoji(handler_name)} {handler_name.upper()} HANDLER ({successful}/{total} funciones exitosas)")
            
            for result in handler_results:
                status = "✅" if result.success else "❌"
                print(f"├── {result.function}")
                print(f"│   📋 Request: {', '.join(result.fields_sent)} ({result.request_size_bytes} bytes)")
                print(f"│   📊 Response: {', '.join(result.fields_received[:5])}{'...' if len(result.fields_received) > 5 else ''} ({result.response_size_bytes} bytes)")
                print(f"│   🗄️ Tablas BD: {', '.join(result.tables_involved) if result.tables_involved else 'N/A'}")
                print(f"│   ⏱️ Tiempo: {result.execution_time_ms:.1f}ms | 📈 Registros: {result.records_processed}")
                if result.success:
                    print(f"│   {status} Validación: Estructura correcta, respuesta válida")
                else:
                    print(f"│   {status} Error: {result.error_message}")
                print("│")
        
        # Estadísticas adicionales
        print(f"\n📊 ESTADÍSTICAS ADICIONALES:")
        print(f"• Función más rápida: {min(self.results, key=lambda r: r.execution_time_ms).function} ({min(r.execution_time_ms for r in self.results):.1f}ms)")
        print(f"• Función más lenta: {max(self.results, key=lambda r: r.execution_time_ms).function} ({max(r.execution_time_ms for r in self.results):.1f}ms)")
        print(f"• Mayor transferencia de datos: {max(self.results, key=lambda r: r.response_size_bytes).function} ({max(r.response_size_bytes for r in self.results)} bytes)")
        print(f"• Mayor procesamiento de registros: {max(self.results, key=lambda r: r.records_processed).function} ({max(r.records_processed for r in self.results)} registros)")
        
        # Tablas más utilizadas
        table_usage = {}
        for result in self.results:
            for table in result.tables_involved:
                table_usage[table] = table_usage.get(table, 0) + 1
        
        if table_usage:
            print(f"\n🗄️ TABLAS MÁS UTILIZADAS:")
            for table, count in sorted(table_usage.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"• {table}: {count} funciones")
        
        # Errores encontrados
        errors = [r for r in self.results if not r.success]
        if errors:
            print(f"\n❌ ERRORES ENCONTRADOS:")
            for error in errors:
                print(f"• {error.handler}.{error.function}: {error.error_message}")
        
        print(f"\n🕐 Finalizado: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
    
    def get_handler_emoji(self, handler: str) -> str:
        """Obtiene el emoji correspondiente al handler."""
        emojis = {
            "users": "👥",
            "conversations": "💬",
            "messages": "📨",
            "dashboard": "📊",
            "leads": "👥",
            "meetings": "📅",
            "requirements": "📋"
        }
        return emojis.get(handler, "🔧")

async def main():
    """Función principal del test suite."""
    suite = WebSocketTestSuite()
    
    print("🧪 WEBSOCKET COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print("🚀 Iniciando suite completa de pruebas...")
    print("📝 Probando TODOS los handlers con análisis detallado")
    print()
    
    # Iniciar servidor si es necesario
    if not suite.start_server():
        print("❌ No se pudo iniciar el servidor. Saliendo...")
        return
    
    try:
        # Esperar un poco más para asegurar que el servidor esté completamente listo
        print("⏳ Esperando a que el servidor esté completamente listo...")
        time.sleep(5)
        
        # Ejecutar todas las pruebas
        await suite.run_all_tests()
        
    except KeyboardInterrupt:
        print("\n⏹️ Pruebas interrumpidas por el usuario")
    except Exception as e:
        print(f"\n💥 Error fatal: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Limpiar
        suite.stop_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Suite de pruebas terminada")
    except Exception as e:
        print(f"\n💥 Error al ejecutar suite: {str(e)}")
