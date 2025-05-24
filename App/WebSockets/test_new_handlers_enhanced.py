"""
🧪 WEBSOCKET ENHANCED DEBUG TEST SUITE
=====================================
Suite mejorada de pruebas con logging detallado, stack traces completos,
métricas de rendimiento y debugging avanzado para identificar errores.
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
import traceback
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import threading
from pathlib import Path

# Configuración
WEBSOCKET_URL = "ws://localhost:8000/ws"
SERVER_URL = "http://localhost:8000"
SERVER_PORT = 8000

# Configurar logging detallado
def setup_logging():
    """Configura el sistema de logging detallado."""
    log_dir = Path("App/WebSockets/logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"websocket_test_{timestamp}.log"
    
    # Configurar logging con múltiples niveles
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d [%(levelname)8s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return log_file

@dataclass
class DetailedTestResult:
    """Resultado detallado de una prueba individual con debugging completo."""
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
    
    # Nuevos campos para debugging detallado
    timestamp: str = ""
    connection_info: Dict[str, Any] = None
    network_latency_ms: float = 0.0
    server_processing_time_ms: float = 0.0
    validation_errors: List[str] = None
    stack_trace: Optional[str] = None
    http_status_equivalent: Optional[int] = None
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    websocket_state: str = ""
    retry_count: int = 0
    expected_fields: List[str] = None
    missing_fields: List[str] = None
    unexpected_fields: List[str] = None
    data_validation_score: float = 0.0

class EnhancedWebSocketTestSuite:
    """Suite mejorada de pruebas WebSocket con debugging avanzado."""
    
    def __init__(self):
        self.results: List[DetailedTestResult] = []
        self.server_process = None
        self.start_time = None
        self.end_time = None
        self.logger = logging.getLogger(__name__)
        self.log_file = setup_logging()
        self.connection_stats = {
            "total_connections": 0,
            "failed_connections": 0,
            "reconnections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "total_bytes_sent": 0,
            "total_bytes_received": 0
        }
        
    def log_system_info(self):
        """Registra información detallada del sistema."""
        self.logger.info("=" * 80)
        self.logger.info("🖥️  INFORMACIÓN DEL SISTEMA")
        self.logger.info("=" * 80)
        
        # Información del sistema
        import platform
        self.logger.info(f"Sistema Operativo: {platform.system()} {platform.release()}")
        self.logger.info(f"Arquitectura: {platform.machine()}")
        self.logger.info(f"Python: {platform.python_version()}")
        
        # Información de memoria y CPU
        memory = psutil.virtual_memory()
        self.logger.info(f"Memoria Total: {memory.total / (1024**3):.1f} GB")
        self.logger.info(f"Memoria Disponible: {memory.available / (1024**3):.1f} GB")
        self.logger.info(f"CPU Cores: {psutil.cpu_count()}")
        self.logger.info(f"CPU Uso: {psutil.cpu_percent()}%")
        
        # Información de red
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            self.logger.info(f"Hostname: {hostname}")
            self.logger.info(f"IP Local: {local_ip}")
        except Exception as e:
            self.logger.warning(f"No se pudo obtener info de red: {e}")
        
        self.logger.info("=" * 80)
        
    def is_server_running(self) -> Tuple[bool, Dict[str, Any]]:
        """Verifica si el servidor está ejecutándose con información detallada."""
        server_info = {
            "running": False,
            "response_time_ms": 0,
            "status_code": None,
            "process_info": None,
            "port_info": None
        }
        
        try:
            start_time = time.time()
            response = requests.get(f"{SERVER_URL}/health-check", timeout=5)
            end_time = time.time()
            
            server_info["running"] = response.status_code == 200
            server_info["response_time_ms"] = (end_time - start_time) * 1000
            server_info["status_code"] = response.status_code
            
            self.logger.info(f"✅ Servidor responde en {server_info['response_time_ms']:.1f}ms")
            return True, server_info
            
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"❌ No se pudo conectar vía HTTP: {e}")
            
            # Verificar procesos en el puerto
            try:
                for conn in psutil.net_connections():
                    if conn.laddr.port == SERVER_PORT:
                        try:
                            process = psutil.Process(conn.pid)
                            server_info["process_info"] = {
                                "pid": conn.pid,
                                "name": process.name(),
                                "status": process.status(),
                                "cpu_percent": process.cpu_percent(),
                                "memory_mb": process.memory_info().rss / (1024**2)
                            }
                            server_info["port_info"] = {
                                "port": conn.laddr.port,
                                "status": conn.status
                            }
                            self.logger.info(f"🔍 Proceso encontrado en puerto {SERVER_PORT}: {process.name()} (PID: {conn.pid})")
                            return True, server_info
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                            
                self.logger.error(f"❌ No hay procesos escuchando en puerto {SERVER_PORT}")
                return False, server_info
                
            except Exception as e:
                self.logger.error(f"❌ Error verificando procesos: {e}")
                return False, server_info
    
    def start_server(self) -> bool:
        """Inicia el servidor WebSocket con logging detallado."""
        self.logger.info("🚀 INICIANDO SERVIDOR WEBSOCKET")
        self.logger.info("-" * 50)
        
        is_running, server_info = self.is_server_running()
        if is_running:
            self.logger.info("✅ Servidor ya está ejecutándose")
            self.logger.info(f"📊 Info del servidor: {json.dumps(server_info, indent=2)}")
            return True
            
        self.logger.info("🔄 Intentando iniciar servidor automáticamente...")
        
        commands = [
            ["uvicorn", "App.api:app", "--host", "0.0.0.0", "--port", "8000"],
            ["python", "-m", "uvicorn", "App.api:app", "--host", "0.0.0.0", "--port", "8000"],
            ["python", "App/api.py"],
            ["python", "-c", "from App.api import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000)"]
        ]
        
        for i, cmd in enumerate(commands, 1):
            try:
                self.logger.info(f"🔄 Intento {i}/{len(commands)}: {' '.join(cmd)}")
                
                self.server_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=os.getcwd(),
                    text=True
                )
                
                # Esperar y monitorear el inicio
                for attempt in range(30):
                    time.sleep(1)
                    
                    # Verificar si el proceso sigue vivo
                    if self.server_process.poll() is not None:
                        stdout, stderr = self.server_process.communicate()
                        self.logger.error(f"❌ Proceso terminó prematuramente")
                        self.logger.error(f"STDOUT: {stdout}")
                        self.logger.error(f"STDERR: {stderr}")
                        break
                    
                    is_running, server_info = self.is_server_running()
                    if is_running:
                        self.logger.info(f"✅ Servidor iniciado exitosamente en {attempt + 1} segundos")
                        self.logger.info(f"📊 Info del servidor: {json.dumps(server_info, indent=2)}")
                        return True
                    
                    if attempt % 5 == 0:
                        self.logger.info(f"⏳ Esperando servidor... ({attempt + 1}/30)")
                
                # Si llegamos aquí, el comando no funcionó
                if self.server_process.poll() is None:
                    self.server_process.terminate()
                    self.server_process.wait()
                self.server_process = None
                
            except Exception as e:
                self.logger.error(f"❌ Error con comando {' '.join(cmd)}: {e}")
                self.logger.error(f"Stack trace: {traceback.format_exc()}")
                continue
        
        self.logger.error("❌ No se pudo iniciar el servidor automáticamente")
        self.logger.error("📝 Por favor, inicia el servidor manualmente:")
        self.logger.error("   uvicorn App.api:app --host 0.0.0.0 --port 8000")
        return False
    
    def stop_server(self):
        """Detiene el servidor con logging detallado."""
        if self.server_process:
            self.logger.info("🛑 Deteniendo servidor...")
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=10)
                self.logger.info("✅ Servidor detenido correctamente")
            except subprocess.TimeoutExpired:
                self.logger.warning("⚠️ Servidor no respondió, forzando cierre...")
                self.server_process.kill()
                self.server_process.wait()
                self.logger.info("✅ Servidor forzado a cerrar")
            except Exception as e:
                self.logger.error(f"❌ Error deteniendo servidor: {e}")
            finally:
                self.server_process = None
    
    async def create_websocket_connection(self) -> websockets.WebSocketServerProtocol:
        """Crea una conexión WebSocket con retry y logging detallado."""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"🔌 Intento de conexión WebSocket {attempt + 1}/{max_retries}")
                
                # Medir tiempo de conexión
                start_time = time.time()
                websocket = await asyncio.wait_for(
                    websockets.connect(WEBSOCKET_URL), 
                    timeout=10.0
                )
                connection_time = (time.time() - start_time) * 1000
                
                self.connection_stats["total_connections"] += 1
                if attempt > 0:
                    self.connection_stats["reconnections"] += 1
                
                self.logger.info(f"✅ Conexión WebSocket establecida en {connection_time:.1f}ms")
                self.logger.info(f"🔗 Estado de conexión: {websocket.state}")
                
                # Recibir mensaje de bienvenida
                try:
                    welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    self.logger.info(f"📨 Mensaje de bienvenida recibido: {welcome_msg[:100]}...")
                    self.connection_stats["total_messages_received"] += 1
                    self.connection_stats["total_bytes_received"] += len(welcome_msg.encode('utf-8'))
                except asyncio.TimeoutError:
                    self.logger.warning("⚠️ No se recibió mensaje de bienvenida")
                
                return websocket
                
            except Exception as e:
                self.connection_stats["failed_connections"] += 1
                self.logger.error(f"❌ Error en conexión WebSocket (intento {attempt + 1}): {e}")
                self.logger.error(f"Stack trace: {traceback.format_exc()}")
                
                if attempt < max_retries - 1:
                    self.logger.info(f"⏳ Esperando {retry_delay}s antes del siguiente intento...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Backoff exponencial
        
        raise Exception(f"No se pudo establecer conexión WebSocket después de {max_retries} intentos")
    
    async def send_message_and_analyze_enhanced(self, websocket, message: Dict[str, Any]) -> DetailedTestResult:
        """Envía un mensaje y analiza la respuesta con debugging completo."""
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Extraer información básica
        handler = message.get("resource", "unknown")
        function = message.get("action", "unknown")
        
        self.logger.info(f"🧪 INICIANDO PRUEBA: {handler}.{function}")
        self.logger.info(f"📋 ID de prueba: {message_id}")
        self.logger.info(f"🕐 Timestamp: {timestamp}")
        
        # Preparar mensaje WebSocket
        payload_data = {"action": function}
        if "payload" in message:
            payload_data.update(message["payload"])
        
        websocket_message = {
            "type": "request",
            "id": message_id,
            "resource": handler,
            "payload": payload_data
        }
        
        # Información de request
        request_json = json.dumps(websocket_message, indent=2)
        request_size = len(request_json.encode('utf-8'))
        fields_sent = list(websocket_message.keys())
        if "payload" in websocket_message:
            fields_sent.extend(list(websocket_message["payload"].keys()))
        
        self.logger.debug(f"📤 REQUEST DATA:\n{request_json}")
        self.logger.info(f"📊 Request size: {request_size} bytes")
        self.logger.info(f"📋 Fields sent: {fields_sent}")
        
        # Obtener métricas del sistema antes
        memory_before = psutil.virtual_memory().percent
        cpu_before = psutil.cpu_percent()
        
        # Información de conexión
        connection_info = {
            "state": str(websocket.state),
            "local_address": getattr(websocket, 'local_address', None),
            "remote_address": getattr(websocket, 'remote_address', None)
        }
        
        start_time = time.time()
        network_start = time.time()
        
        try:
            # Enviar mensaje
            await websocket.send(request_json)
            network_send_time = (time.time() - network_start) * 1000
            
            self.connection_stats["total_messages_sent"] += 1
            self.connection_stats["total_bytes_sent"] += request_size
            
            self.logger.info(f"📤 Mensaje enviado en {network_send_time:.1f}ms")
            
            # Recibir respuesta con timeout
            response_start = time.time()
            response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
            network_latency = (time.time() - response_start) * 1000
            
            self.connection_stats["total_messages_received"] += 1
            self.connection_stats["total_bytes_received"] += len(response.encode('utf-8'))
            
            end_time = time.time()
            total_execution_time = (end_time - start_time) * 1000
            
            self.logger.info(f"📥 Respuesta recibida en {network_latency:.1f}ms")
            self.logger.info(f"⏱️ Tiempo total: {total_execution_time:.1f}ms")
            
            # Parsear respuesta
            try:
                response_data = json.loads(response)
                self.logger.debug(f"📥 RESPONSE DATA:\n{json.dumps(response_data, indent=2)}")
            except json.JSONDecodeError as e:
                self.logger.error(f"❌ Error parseando JSON: {e}")
                self.logger.error(f"Raw response: {response}")
                raise
            
            response_size = len(response.encode('utf-8'))
            self.logger.info(f"📊 Response size: {response_size} bytes")
            
            # Análisis de respuesta
            success = response_data.get("type") != "error"
            fields_received = []
            records_processed = 0
            validation_errors = []
            
            # Análisis detallado de campos
            if "payload" in response_data:
                payload = response_data["payload"]
                if isinstance(payload, dict):
                    fields_received = list(payload.keys())
                    
                    # Contar registros procesados
                    for key, value in payload.items():
                        if isinstance(value, list):
                            records_processed = max(records_processed, len(value))
                            if value and isinstance(value[0], dict):
                                fields_received.extend(list(value[0].keys()))
                        elif isinstance(value, dict):
                            records_processed = max(records_processed, 1)
                            fields_received.extend(list(value.keys()))
            
            # Validación de campos esperados
            expected_fields = self.get_expected_fields(handler, function)
            missing_fields = [f for f in expected_fields if f not in fields_received]
            unexpected_fields = [f for f in fields_received if f not in expected_fields and f not in ['id', 'type', 'payload']]
            
            if missing_fields:
                validation_errors.append(f"Campos faltantes: {missing_fields}")
            if unexpected_fields:
                validation_errors.append(f"Campos inesperados: {unexpected_fields}")
            
            # Calcular score de validación
            if expected_fields:
                data_validation_score = (len(expected_fields) - len(missing_fields)) / len(expected_fields) * 100
            else:
                data_validation_score = 100.0 if success else 0.0
            
            # Métricas del sistema después
            memory_after = psutil.virtual_memory().percent
            cpu_after = psutil.cpu_percent()
            
            # Determinar tiempo de procesamiento del servidor
            server_processing_time = total_execution_time - network_latency
            
            # Mapear a código HTTP equivalente
            http_status_equivalent = 200 if success else 500
            if not success and "not found" in str(response_data.get("payload", {}).get("message", "")).lower():
                http_status_equivalent = 404
            elif not success and "unauthorized" in str(response_data.get("payload", {}).get("message", "")).lower():
                http_status_equivalent = 401
            
            self.logger.info(f"✅ Análisis completado - Success: {success}")
            self.logger.info(f"📊 Validation score: {data_validation_score:.1f}%")
            self.logger.info(f"📈 Records processed: {records_processed}")
            
            return DetailedTestResult(
                handler=handler,
                function=function,
                success=success,
                request_data=message,
                response_data=response_data,
                execution_time_ms=total_execution_time,
                request_size_bytes=request_size,
                response_size_bytes=response_size,
                tables_involved=self.get_tables_for_function(handler, function),
                fields_sent=fields_sent,
                fields_received=list(set(fields_received)),
                records_processed=records_processed,
                error_message=response_data.get("payload", {}).get("message") if not success else None,
                timestamp=timestamp,
                connection_info=connection_info,
                network_latency_ms=network_latency,
                server_processing_time_ms=server_processing_time,
                validation_errors=validation_errors,
                stack_trace=None,
                http_status_equivalent=http_status_equivalent,
                memory_usage_mb=(memory_after - memory_before),
                cpu_usage_percent=(cpu_after - cpu_before),
                websocket_state=str(websocket.state),
                retry_count=0,
                expected_fields=expected_fields,
                missing_fields=missing_fields,
                unexpected_fields=unexpected_fields,
                data_validation_score=data_validation_score
            )
            
        except asyncio.TimeoutError:
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            
            error_msg = f"Timeout después de 15 segundos"
            self.logger.error(f"⏰ {error_msg}")
            
            return DetailedTestResult(
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
                error_message=error_msg,
                timestamp=timestamp,
                connection_info=connection_info,
                network_latency_ms=0,
                server_processing_time_ms=0,
                validation_errors=[error_msg],
                stack_trace=traceback.format_exc(),
                http_status_equivalent=408,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                websocket_state=str(websocket.state),
                retry_count=0,
                expected_fields=[],
                missing_fields=[],
                unexpected_fields=[],
                data_validation_score=0.0
            )
            
        except Exception as e:
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            
            self.logger.error(f"💥 Error durante la prueba: {error_msg}")
            self.logger.error(f"Stack trace completo:\n{stack_trace}")
            
            return DetailedTestResult(
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
                error_message=error_msg,
                timestamp=timestamp,
                connection_info=connection_info,
                network_latency_ms=0,
                server_processing_time_ms=0,
                validation_errors=[error_msg],
                stack_trace=stack_trace,
                http_status_equivalent=500,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                websocket_state=str(websocket.state),
                retry_count=0,
                expected_fields=[],
                missing_fields=[],
                unexpected_fields=[],
                data_validation_score=0.0
            )
    
    def get_expected_fields(self, handler: str, function: str) -> List[str]:
        """Define los campos esperados para cada función."""
        expected_fields_map = {
            "users": {
                "get_all_users": ["users"],
                "create_user": ["user"],
                "get_user_by_id": ["user"],
                "update_user": ["user"],
                "delete_user": ["deleted"]
            },
            "conversations": {
                "get_all_conversations": ["conversations"],
                "create_conversation": ["conversation"],
                "get_conversation_by_id": ["conversation"],
                "close_conversation": ["conversation"],
                "update_agent_status": ["conversation"],
                "get_user_conversations": ["conversations"]
            },
            "messages": {
                "get_all_messages": ["messages"],
                "send_message": ["message"],
                "get_conversation_messages": ["messages"],
                "mark_as_read": ["updated_count"],
                "delete_message": ["deleted"],
                "update_message": ["message"]
            },
            "dashboard": {
                "get_dashboard_stats": ["stats"],
                "get_conversion_funnel": ["funnel"],
                "get_activity_timeline": ["timeline"],
                "get_agent_performance": ["performance"],
                "get_real_time_metrics": ["real_time_metrics"]
            },
            "leads": {
                "get_all_leads": ["leads"],
                "get_lead_pipeline": ["pipeline"],
                "get_lead_with_complete_data": ["lead"],
                "update_lead_step": ["lead"],
                "get_conversion_stats": ["conversion_stats"],
                "get_abandoned_leads": ["abandoned_leads"]
            },
            "meetings": {
                "get_all_meetings": ["meetings"],
                "get_calendar_view": ["calendar"],
                "create_meeting": ["meeting"],
                "update_meeting": ["meeting"],
                "cancel_meeting": ["meeting"],
                "get_available_slots": ["available_slots"],
                "sync_outlook_calendar": ["sync_result"]
            },
            "requirements": {
                "get_requirements_by_lead": ["requirements"],
                "create_requirement_package": ["requirement"],
                "update_requirements": ["requirement"],
                "add_feature": ["feature"],
                "add_integration": ["integration"],
                "get_popular_features": ["popular_features"],
                "get_popular_integrations": ["popular_integrations"]
            }
        }
        
        return expected_fields_map.get(handler, {}).get(function, [])
    
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
    
    async def run_all_tests_enhanced(self):
        """Ejecuta todas las pruebas con logging y debugging mejorado."""
        self.start_time = datetime.now()
        
        self.logger.info("🧪 WEBSOCKET ENHANCED DEBUG TEST SUITE")
        self.logger.info("=" * 80)
        self.logger.info(f"🕐 Inicio: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"📁 Log file: {self.log_file}")
        
        # Registrar información del sistema
        self.log_system_info()
        
        try:
            # Crear conexión WebSocket con retry
            websocket = await self.create_websocket_connection()
            
            self.logger.info("✅ Conexión WebSocket establecida, iniciando pruebas...")
            self.logger.info("-" * 80)
            
            # Ejecutar pruebas por handler con logging detallado
            await self.test_users_handler_enhanced(websocket)
            await self.test_conversations_handler_enhanced(websocket)
            await self.test_messages_handler_enhanced(websocket)
            await self.test_dashboard_handler_enhanced(websocket)
            await self.test_leads_handler_enhanced(websocket)
            await self.test_meetings_handler_enhanced(websocket)
            await self.test_requirements_handler_enhanced(websocket)
            
            await websocket.close()
            self.logger.info("🔌 Conexión WebSocket cerrada")
            
        except Exception as e:
            self.logger.error(f"💥 Error fatal durante las pruebas: {str(e)}")
            self.logger.error(f"Stack trace completo:\n{traceback.format_exc()}")
        
        self.end_time = datetime.now()
        self.generate_enhanced_report()
    
    # ========== PRUEBAS MEJORADAS POR HANDLER ==========
    
    async def test_users_handler_enhanced(self, websocket):
        """Prueba todas las funciones del UsersHandler con debugging mejorado."""
        self.logger.info("👥 === TESTING USERS HANDLER (ENHANCED) ===")
        
        test_user_id = str(uuid.uuid4())
        
        tests = [
            {"resource": "users", "action": "get_all_users"},
            {"resource": "users", "action": "create_user", "payload": {
                "user": {
                    "full_name": f"Usuario Test Enhanced {datetime.now().strftime('%H%M%S')}", 
                    "email": f"test_enhanced_{int(time.time())}@test.com", 
                    "phone": f"+1{int(time.time())}", 
                    "company": "Enhanced Test Corp"
                }
            }},
            {"resource": "users", "action": "get_user_by_id", "payload": {"user_id": test_user_id}},
            {"resource": "users", "action": "update_user", "payload": {
                "user_id": test_user_id,
                "user": {"full_name": "Usuario Actualizado Enhanced"}
            }},
            {"resource": "users", "action": "delete_user", "payload": {"user_id": test_user_id}}
        ]
        
        for test in tests:
            result = await self.send_message_and_analyze_enhanced(websocket, test)
            self.results.append(result)
            status = "✅" if result.success else "❌"
            self.logger.info(f"{status} {result.function} - {result.execution_time_ms:.1f}ms - Score: {result.data_validation_score:.1f}%")
        
        self.logger.info("👥 Users Handler testing completed\n")
    
    async def test_conversations_handler_enhanced(self, websocket):
        """Prueba todas las funciones del ConversationsHandler con debugging mejorado."""
        self.logger.info("💬 === TESTING CONVERSATIONS HANDLER (ENHANCED) ===")
        
        test_user_id = str(uuid.uuid4())
        test_conv_id = str(uuid.uuid4())
        
        tests = [
            {"resource": "conversations", "action": "get_all_conversations", "payload": {"user_id": test_user_id}},
            {"resource": "conversations", "action": "create_conversation", "payload": {
                "user_id": test_user_id, "external_id": f"+1{int(time.time())}", "platform": "whatsapp"
            }},
            {"resource": "conversations", "action": "get_conversation_by_id", "payload": {"conversation_id": test_conv_id}},
            {"resource": "conversations", "action": "close_conversation", "payload": {"conversation_id": test_conv_id}},
            {"resource": "conversations", "action": "update_agent_status", "payload": {
                "conversation_id": test_conv_id, "enabled": True
            }},
            {"resource": "conversations", "action": "get_user_conversations", "payload": {"user_id": test_user_id}}
        ]
        
        for test in tests:
            result = await self.send_message_and_analyze_enhanced(websocket, test)
            self.results.append(result)
            status = "✅" if result.success else "❌"
            self.logger.info(f"{status} {result.function} - {result.execution_time_ms:.1f}ms - Score: {result.data_validation_score:.1f}%")
        
        self.logger.info("💬 Conversations Handler testing completed\n")
    
    async def test_messages_handler_enhanced(self, websocket):
        """Prueba todas las funciones del MessagesHandler con debugging mejorado."""
        self.logger.info("📨 === TESTING MESSAGES HANDLER (ENHANCED) ===")
        
        test_conv_id = str(uuid.uuid4())
        test_msg_id = str(uuid.uuid4())
        
        tests = [
            {"resource": "messages", "action": "get_all_messages", "payload": {"conversation_id": test_conv_id}},
            {"resource": "messages", "action": "send_message", "payload": {
                "conversation_id": test_conv_id, "content": f"Mensaje de prueba enhanced {datetime.now()}", "role": "user"
            }},
            {"resource": "messages", "action": "get_conversation_messages", "payload": {"conversation_id": test_conv_id}},
            {"resource": "messages", "action": "mark_as_read", "payload": {"conversation_id": test_conv_id}},
            {"resource": "messages", "action": "delete_message", "payload": {"message_id": test_msg_id}},
            {"resource": "messages", "action": "update_message", "payload": {
                "message_id": test_msg_id, "content": "Mensaje actualizado enhanced"
            }}
        ]
        
        for test in tests:
            result = await self.send_message_and_analyze_enhanced(websocket, test)
            self.results.append(result)
            status = "✅" if result.success else "❌"
            self.logger.info(f"{status} {result.function} - {result.execution_time_ms:.1f}ms - Score: {result.data_validation_score:.1f}%")
        
        self.logger.info("📨 Messages Handler testing completed\n")
    
    async def test_dashboard_handler_enhanced(self, websocket):
        """Prueba todas las funciones del DashboardHandler con debugging mejorado."""
        self.logger.info("📊 === TESTING DASHBOARD HANDLER (ENHANCED) ===")
        
        tests = [
            {"resource": "dashboard", "action": "get_dashboard_stats"},
            {"resource": "dashboard", "action": "get_conversion_funnel"},
            {"resource": "dashboard", "action": "get_activity_timeline"},
            {"resource": "dashboard", "action": "get_agent_performance"},
            {"resource": "dashboard", "action": "get_real_time_metrics"}
        ]
        
        for test in tests:
            result = await self.send_message_and_analyze_enhanced(websocket, test)
            self.results.append(result)
            status = "✅" if result.success else "❌"
            self.logger.info(f"{status} {result.function} - {result.execution_time_ms:.1f}ms - Score: {result.data_validation_score:.1f}%")
        
        self.logger.info("📊 Dashboard Handler testing completed\n")
    
    async def test_leads_handler_enhanced(self, websocket):
        """Prueba todas las funciones del LeadsHandler con debugging mejorado."""
        self.logger.info("👥 === TESTING LEADS HANDLER (ENHANCED) ===")
        
        test_lead_id = str(uuid.uuid4())
        
        tests = [
            {"resource": "leads", "action": "get_all_leads"},
            {"resource": "leads", "action": "get_lead_pipeline"},
            {"resource": "leads", "action": "get_lead_with_complete_data", "payload": {"lead_id": test_lead_id}},
            {"resource": "leads", "action": "update_lead_step", "payload": {
                "lead_id": test_lead_id, "current_step": "requirements"
            }},
            {"resource": "leads", "action": "get_conversion_stats"},
            {"resource": "leads", "action": "get_abandoned_leads"}
        ]
        
        for test in tests:
            result = await self.send_message_and_analyze_enhanced(websocket, test)
            self.results.append(result)
            status = "✅" if result.success else "❌"
            self.logger.info(f"{status} {result.function} - {result.execution_time_ms:.1f}ms - Score: {result.data_validation_score:.1f}%")
        
        self.logger.info("👥 Leads Handler testing completed\n")
    
    async def test_meetings_handler_enhanced(self, websocket):
        """Prueba todas las funciones del MeetingsHandler con debugging mejorado."""
        self.logger.info("📅 === TESTING MEETINGS HANDLER (ENHANCED) ===")
        
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
                "meeting": {
                    "user_id": test_user_id, 
                    "lead_qualification_id": test_lead_id,
                    "subject": f"Reunión de prueba enhanced {datetime.now().strftime('%H:%M:%S')}", 
                    "start_time": (datetime.now() + timedelta(days=1)).isoformat(),
                    "end_time": (datetime.now() + timedelta(days=1, hours=1)).isoformat()
                }
            }},
            {"resource": "meetings", "action": "update_meeting", "payload": {
                "meeting_id": test_meeting_id, 
                "meeting": {"subject": "Reunión actualizada enhanced"}
            }},
            {"resource": "meetings", "action": "cancel_meeting", "payload": {
                "meeting_id": test_meeting_id, "reason": "Prueba enhanced"
            }},
            {"resource": "meetings", "action": "get_available_slots", "payload": {
                "date": datetime.now().strftime("%Y-%m-%d"), "duration_minutes": 60
            }},
            {"resource": "meetings", "action": "sync_outlook_calendar"}
        ]
        
        for test in tests:
            result = await self.send_message_and_analyze_enhanced(websocket, test)
            self.results.append(result)
            status = "✅" if result.success else "❌"
            self.logger.info(f"{status} {result.function} - {result.execution_time_ms:.1f}ms - Score: {result.data_validation_score:.1f}%")
        
        self.logger.info("📅 Meetings Handler testing completed\n")
    
    async def test_requirements_handler_enhanced(self, websocket):
        """Prueba todas las funciones del RequirementsHandler con debugging mejorado."""
        self.logger.info("📋 === TESTING REQUIREMENTS HANDLER (ENHANCED) ===")
        
        test_lead_id = str(uuid.uuid4())
        test_req_id = str(uuid.uuid4())
        
        tests = [
            {"resource": "requirements", "action": "get_requirements_by_lead", "payload": {"lead_id": test_lead_id}},
            {"resource": "requirements", "action": "create_requirement_package", "payload": {
                "lead_qualification_id": test_lead_id, "app_type": "web_app", 
                "deadline": (datetime.now() + timedelta(days=90)).strftime("%Y-%m-%d"),
                "features": [{"name": "Login Enhanced", "description": "Sistema de autenticación mejorado"}],
                "integrations": [{"name": "PayPal Enhanced", "description": "Procesamiento de pagos mejorado"}]
            }},
            {"resource": "requirements", "action": "update_requirements", "payload": {
                "requirements_id": test_req_id, "app_type": "mobile_app", 
                "deadline": (datetime.now() + timedelta(days=120)).strftime("%Y-%m-%d")
            }},
            {"resource": "requirements", "action": "add_feature", "payload": {
                "requirements_id": test_req_id, "name": "Chat Enhanced", "description": "Chat en tiempo real mejorado"
            }},
            {"resource": "requirements", "action": "add_integration", "payload": {
                "requirements_id": test_req_id, "name": "Stripe Enhanced", "description": "Pagos con tarjeta mejorados"
            }},
            {"resource": "requirements", "action": "get_popular_features"},
            {"resource": "requirements", "action": "get_popular_integrations"}
        ]
        
        for test in tests:
            result = await self.send_message_and_analyze_enhanced(websocket, test)
            self.results.append(result)
            status = "✅" if result.success else "❌"
            self.logger.info(f"{status} {result.function} - {result.execution_time_ms:.1f}ms - Score: {result.data_validation_score:.1f}%")
        
        self.logger.info("📋 Requirements Handler testing completed\n")
    
    def generate_enhanced_report(self):
        """Genera un reporte completo y detallado con debugging avanzado."""
        self.logger.info("\n" + "=" * 100)
        self.logger.info("📊 REPORTE COMPLETO ENHANCED - WEBSOCKET DEBUG TEST SUITE")
        self.logger.info("=" * 100)
        
        # Resumen ejecutivo mejorado
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests
        total_time = (self.end_time - self.start_time).total_seconds()
        avg_response_time = sum(r.execution_time_ms for r in self.results) / total_tests if total_tests > 0 else 0
        avg_validation_score = sum(r.data_validation_score for r in self.results) / total_tests if total_tests > 0 else 0
        
        self.logger.info(f"\n📈 RESUMEN EJECUTIVO ENHANCED:")
        self.logger.info("┌" + "─" * 98 + "┐")
        self.logger.info(f"│ Total Handlers Probados: {len(set(r.handler for r in self.results)):<70} │")
        self.logger.info(f"│ Total Funciones Probadas: {total_tests:<69} │")
        self.logger.info(f"│ Pruebas Exitosas: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%){'':<50} │")
        self.logger.info(f"│ Pruebas Fallidas: {failed_tests}/{total_tests} ({failed_tests/total_tests*100:.1f}%){'':<51} │")
        self.logger.info(f"│ Tiempo Total de Ejecución: {total_time:.1f} segundos{'':<55} │")
        self.logger.info(f"│ Promedio Tiempo Respuesta: {avg_response_time:.1f}ms{'':<60} │")
        self.logger.info(f"│ Promedio Score Validación: {avg_validation_score:.1f}%{'':<59} │")
        self.logger.info(f"│ Total Datos Transferidos: {self.connection_stats['total_bytes_sent']/1024:.1f} KB enviados, {self.connection_stats['total_bytes_received']/1024:.1f} KB recibidos{'':<20} │")
        self.logger.info(f"│ Conexiones WebSocket: {self.connection_stats['total_connections']} exitosas, {self.connection_stats['failed_connections']} fallidas{'':<35} │")
        self.logger.info("└" + "─" * 98 + "┘")
        
        # Análisis detallado de errores
        errors = [r for r in self.results if not r.success]
        if errors:
            self.logger.info(f"\n❌ ANÁLISIS DETALLADO DE ERRORES ({len(errors)} errores encontrados):")
            for i, error in enumerate(errors, 1):
                self.logger.info(f"\n🔍 ERROR #{i}: {error.handler}.{error.function}")
                self.logger.info(f"   📋 Mensaje: {error.error_message}")
                self.logger.info(f"   🕐 Timestamp: {error.timestamp}")
                self.logger.info(f"   ⏱️ Tiempo ejecución: {error.execution_time_ms:.1f}ms")
                self.logger.info(f"   🌐 HTTP equivalente: {error.http_status_equivalent}")
                self.logger.info(f"   🔗 Estado WebSocket: {error.websocket_state}")
                if error.validation_errors:
                    self.logger.info(f"   ⚠️ Errores validación: {', '.join(error.validation_errors)}")
                if error.missing_fields:
                    self.logger.info(f"   📋 Campos faltantes: {error.missing_fields}")
                if error.stack_trace:
                    self.logger.info(f"   🔍 Stack trace:\n{error.stack_trace}")
        
        # Métricas de rendimiento
        self.logger.info(f"\n⚡ MÉTRICAS DE RENDIMIENTO:")
        if self.results:
            fastest = min(self.results, key=lambda r: r.execution_time_ms)
            slowest = max(self.results, key=lambda r: r.execution_time_ms)
            best_validation = max(self.results, key=lambda r: r.data_validation_score)
            worst_validation = min(self.results, key=lambda r: r.data_validation_score)
            
            self.logger.info(f"• Función más rápida: {fastest.handler}.{fastest.function} ({fastest.execution_time_ms:.1f}ms)")
            self.logger.info(f"• Función más lenta: {slowest.handler}.{slowest.function} ({slowest.execution_time_ms:.1f}ms)")
            self.logger.info(f"• Mejor validación: {best_validation.handler}.{best_validation.function} ({best_validation.data_validation_score:.1f}%)")
            self.logger.info(f"• Peor validación: {worst_validation.handler}.{worst_validation.function} ({worst_validation.data_validation_score:.1f}%)")
        
        # Estadísticas de conexión
        self.logger.info(f"\n🔌 ESTADÍSTICAS DE CONEXIÓN:")
        self.logger.info(f"• Total conexiones: {self.connection_stats['total_connections']}")
        self.logger.info(f"• Conexiones fallidas: {self.connection_stats['failed_connections']}")
        self.logger.info(f"• Reconexiones: {self.connection_stats['reconnections']}")
        self.logger.info(f"• Mensajes enviados: {self.connection_stats['total_messages_sent']}")
        self.logger.info(f"• Mensajes recibidos: {self.connection_stats['total_messages_received']}")
        
        # Resumen por handler
        self.logger.info(f"\n📊 RESUMEN POR HANDLER:")
        handlers = {}
        for result in self.results:
            if result.handler not in handlers:
                handlers[result.handler] = []
            handlers[result.handler].append(result)
        
        for handler_name, handler_results in handlers.items():
            successful = sum(1 for r in handler_results if r.success)
            total = len(handler_results)
            avg_time = sum(r.execution_time_ms for r in handler_results) / total
            avg_score = sum(r.data_validation_score for r in handler_results) / total
            
            self.logger.info(f"\n🔧 {handler_name.upper()}: {successful}/{total} exitosas, {avg_time:.1f}ms promedio, {avg_score:.1f}% validación")
            
            for result in handler_results:
                status = "✅" if result.success else "❌"
                self.logger.info(f"   {status} {result.function}: {result.execution_time_ms:.1f}ms, {result.data_validation_score:.1f}% validación")
                if not result.success:
                    self.logger.info(f"      💥 Error: {result.error_message}")
        
        self.logger.info(f"\n🕐 Finalizado: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"📁 Log completo guardado en: {self.log_file}")
        self.logger.info("=" * 100)

async def main_enhanced():
    """Función principal del test suite mejorado."""
    suite = EnhancedWebSocketTestSuite()
    
    print("🧪 WEBSOCKET ENHANCED DEBUG TEST SUITE")
    print("=" * 80)
    print("🚀 Iniciando suite mejorada con debugging avanzado...")
    print("📝 Probando TODOS los handlers con análisis detallado y logging completo")
    print(f"📁 Los logs se guardarán en: {suite.log_file}")
    print()
    
    # Iniciar servidor si es necesario
    if not suite.start_server():
        print("❌ No se pudo iniciar el servidor. Saliendo...")
        return
    
    try:
        # Esperar a que el servidor esté completamente listo
        print("⏳ Esperando a que el servidor esté completamente listo...")
        time.sleep(5)
        
        # Ejecutar todas las pruebas mejoradas
        await suite.run_all_tests_enhanced()
        
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
        asyncio.run(main_enhanced())
    except KeyboardInterrupt:
        print("\n⏹️ Suite de pruebas enhanced terminada")
    except Exception as e:
        print(f"\n💥 Error al ejecutar suite enhanced: {str(e)}")
