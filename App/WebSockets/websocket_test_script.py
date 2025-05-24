#!/usr/bin/env python3
"""
Script de diagnóstico para WebSocket en Render
Identifica problemas comunes y prueba diferentes configuraciones
"""

import asyncio
import aiohttp
import json
import logging
import time
import os
from datetime import datetime
from typing import Dict, Any, Optional
import traceback
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebSocketDiagnostic:
    def __init__(self, base_url: str = "https://waagentv1.onrender.com"):
        self.base_url = base_url
        self.wss_url = base_url.replace("https://", "wss://").replace("http://", "ws://")
        self.token = os.getenv("WEBSOCKET_AUTH_TOKEN")
        self.results = []
        
    def log_result(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Registra el resultado de una prueba"""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {details}")
        
        self.results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def test_basic_http_connectivity(self):
        """Prueba 1: Conectividad HTTP básica"""
        logger.info("\n" + "="*50)
        logger.info("🧪 PRUEBA 1: CONECTIVIDAD HTTP BÁSICA")
        logger.info("="*50)
        
        try:
            async with aiohttp.ClientSession() as session:
                # Probar endpoint raíz
                async with session.get(f"{self.base_url}/") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log_result("Conectividad HTTP", True, 
                                       f"Status: {response.status}, Response: {data}")
                    else:
                        self.log_result("Conectividad HTTP", False, 
                                       f"Status: {response.status}")
        except Exception as e:
            self.log_result("Conectividad HTTP", False, f"Error: {str(e)}")
    
    async def test_health_check(self):
        """Prueba 2: Health check del servidor"""
        logger.info("\n" + "="*50)
        logger.info("🧪 PRUEBA 2: HEALTH CHECK")
        logger.info("="*50)
        
        endpoints_to_test = [
            "/health-check",
            "/health",
            "/status",
            "/ping"
        ]
        
        for endpoint in endpoints_to_test:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 200:
                            try:
                                data = await response.json()
                                self.log_result(f"Health check {endpoint}", True, 
                                               f"Status: {response.status}, Data: {json.dumps(data, indent=2)}")
                                break
                            except:
                                text = await response.text()
                                self.log_result(f"Health check {endpoint}", True, 
                                               f"Status: {response.status}, Text: {text}")
                                break
                        else:
                            self.log_result(f"Health check {endpoint}", False, 
                                           f"Status: {response.status}")
            except Exception as e:
                self.log_result(f"Health check {endpoint}", False, f"Error: {str(e)}")
    
    async def test_websocket_endpoint_discovery(self):
        """Prueba 3: Descubrimiento de endpoint WebSocket"""
        logger.info("\n" + "="*50)
        logger.info("🧪 PRUEBA 3: DESCUBRIMIENTO DE ENDPOINT WEBSOCKET")
        logger.info("="*50)
        
        possible_endpoints = [
            "/ws",
            "/websocket",
            "/socket.io",
            "/realtime",
            "/api/ws",
            "/api/websocket"
        ]
        
        for endpoint in possible_endpoints:
            try:
                # Probar HTTP GET primero para ver si el endpoint existe
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status in [426, 400]:  # Upgrade Required o Bad Request
                            self.log_result(f"WebSocket endpoint {endpoint}", True, 
                                           f"HTTP {response.status} - Endpoint WebSocket detectado")
                        elif response.status == 404:
                            self.log_result(f"WebSocket endpoint {endpoint}", False, 
                                           f"HTTP 404 - Endpoint no encontrado")
                        else:
                            self.log_result(f"WebSocket endpoint {endpoint}", False, 
                                           f"HTTP {response.status} - Respuesta inesperada")
            except Exception as e:
                self.log_result(f"WebSocket endpoint {endpoint}", False, f"Error: {str(e)}")
    
    async def test_websocket_upgrade_headers(self):
        """Prueba 4: Headers de upgrade WebSocket"""
        logger.info("\n" + "="*50)
        logger.info("🧪 PRUEBA 4: HEADERS DE UPGRADE WEBSOCKET")
        logger.info("="*50)
        
        headers = {
            'Connection': 'Upgrade',
            'Upgrade': 'websocket',
            'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
            'Sec-WebSocket-Version': '13'
        }
        
        endpoints_to_test = ["/ws", "/websocket", "/socket.io"]
        
        for endpoint in endpoints_to_test:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}{endpoint}", headers=headers) as response:
                        response_headers = dict(response.headers)
                        
                        if response.status == 101:
                            self.log_result(f"WebSocket upgrade {endpoint}", True, 
                                           f"Status: {response.status} - Upgrade exitoso")
                        elif response.status == 426:
                            self.log_result(f"WebSocket upgrade {endpoint}", True, 
                                           f"Status: {response.status} - Upgrade requerido detectado")
                        else:
                            self.log_result(f"WebSocket upgrade {endpoint}", False, 
                                           f"Status: {response.status}, Headers: {response_headers}")
            except Exception as e:
                self.log_result(f"WebSocket upgrade {endpoint}", False, f"Error: {str(e)}")
    
    async def test_websocket_libraries(self):
        """Prueba 5: Diferentes librerías WebSocket"""
        logger.info("\n" + "="*50)
        logger.info("🧪 PRUEBA 5: PRUEBA CON DIFERENTES LIBRERÍAS WEBSOCKET")
        logger.info("="*50)
        
        # Probar con websockets library
        try:
            import websockets
            
            endpoints = ["/ws", "/websocket", "/socket.io"]
            
            for endpoint in endpoints:
                ws_url = f"{self.wss_url}{endpoint}"
                if self.token:
                    ws_url += f"?token={self.token}"
                
                try:
                    logger.info(f"🔌 Probando websockets library en: {ws_url}")
                    
                    # Intentar conexión con timeout corto
                    websocket = await asyncio.wait_for(
                        websockets.connect(ws_url), 
                        timeout=10.0
                    )
                    
                    self.log_result(f"websockets library {endpoint}", True, 
                                   f"Conexión exitosa a {ws_url}")
                    
                    # Cerrar conexión inmediatamente
                    await websocket.close()
                    return  # Si funciona, no probar más endpoints
                    
                except asyncio.TimeoutError:
                    self.log_result(f"websockets library {endpoint}", False, 
                                   f"Timeout conectando a {ws_url}")
                except Exception as e:
                    self.log_result(f"websockets library {endpoint}", False, 
                                   f"Error: {str(e)}")
                    
        except ImportError:
            self.log_result("websockets library", False, "Librería websockets no instalada")
        
        # Probar con aiohttp ClientSession WebSocket
        try:
            endpoints = ["/ws", "/websocket", "/socket.io"]
            
            for endpoint in endpoints:
                ws_url = f"{self.wss_url}{endpoint}"
                
                try:
                    logger.info(f"🔌 Probando aiohttp WebSocket en: {ws_url}")
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.ws_connect(ws_url) as ws:
                            self.log_result(f"aiohttp WebSocket {endpoint}", True, 
                                           f"Conexión exitosa a {ws_url}")
                            return  # Si funciona, no probar más endpoints
                            
                except Exception as e:
                    self.log_result(f"aiohttp WebSocket {endpoint}", False, 
                                   f"Error: {str(e)}")
                    
        except Exception as e:
            self.log_result("aiohttp WebSocket", False, f"Error general: {str(e)}")
    
    async def test_render_specific_issues(self):
        """Prueba 6: Problemas específicos de Render"""
        logger.info("\n" + "="*50)
        logger.info("🧪 PRUEBA 6: PROBLEMAS ESPECÍFICOS DE RENDER")
        logger.info("="*50)
        
        # Verificar si el servidor está usando el puerto correcto
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health-check") as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Buscar información sobre WebSocket en la respuesta
                        websocket_info = None
                        if 'integrations' in data and 'websocket' in data['integrations']:
                            websocket_info = data['integrations']['websocket']
                        
                        self.log_result("Render WebSocket Config", 
                                       websocket_info is not None,
                                       f"WebSocket info: {websocket_info}")
                        
                        # Verificar puertos
                        port_info = data.get('port_info', 'No disponible')
                        self.log_result("Render Port Info", True, f"Puerto: {port_info}")
                        
        except Exception as e:
            self.log_result("Render WebSocket Config", False, f"Error: {str(e)}")
        
        # Probar conectividad sin SSL (para debug)
        try:
            http_url = self.base_url.replace("https://", "http://")
            ws_url = http_url.replace("http://", "ws://") + "/ws"
            
            logger.info(f"🔓 Probando conexión insegura: {ws_url}")
            
            import websockets
            websocket = await asyncio.wait_for(
                websockets.connect(ws_url), 
                timeout=5.0
            )
            
            self.log_result("Conexión HTTP insegura", True, 
                           f"Conexión exitosa a {ws_url}")
            await websocket.close()
            
        except Exception as e:
            self.log_result("Conexión HTTP insegura", False, f"Error: {str(e)}")
    
    async def test_alternative_protocols(self):
        """Prueba 7: Protocolos alternativos"""
        logger.info("\n" + "="*50)
        logger.info("🧪 PRUEBA 7: PROTOCOLOS ALTERNATIVOS")
        logger.info("="*50)
        
        # Probar Server-Sent Events
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Accept': 'text/event-stream'}
                async with session.get(f"{self.base_url}/events", headers=headers) as response:
                    if response.status == 200:
                        self.log_result("Server-Sent Events", True, 
                                       f"SSE disponible en /events")
                    else:
                        self.log_result("Server-Sent Events", False, 
                                       f"Status: {response.status}")
        except Exception as e:
            self.log_result("Server-Sent Events", False, f"Error: {str(e)}")
        
        # Probar Socket.IO con polling
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/socket.io/?EIO=4&transport=polling") as response:
                    if response.status == 200:
                        self.log_result("Socket.IO Polling", True, 
                                       f"Socket.IO polling disponible")
                    else:
                        self.log_result("Socket.IO Polling", False, 
                                       f"Status: {response.status}")
        except Exception as e:
            self.log_result("Socket.IO Polling", False, f"Error: {str(e)}")
    
    def generate_diagnosis_report(self):
        """Genera un reporte de diagnóstico"""
        logger.info("\n" + "="*60)
        logger.info("📊 REPORTE DE DIAGNÓSTICO WEBSOCKET")
        logger.info("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"📈 Estadísticas:")
        logger.info(f"   Total de pruebas: {total_tests}")
        logger.info(f"   ✅ Exitosas: {passed_tests}")
        logger.info(f"   ❌ Fallidas: {failed_tests}")
        logger.info(f"   📊 Tasa de éxito: {success_rate:.1f}%")
        
        logger.info(f"\n🔍 Análisis de problemas:")
        
        # Analizar patrones de fallo
        websocket_endpoints_failed = [r for r in self.results 
                                     if "WebSocket endpoint" in r["test"] and not r["success"]]
        
        if websocket_endpoints_failed:
            logger.info("   🚨 PROBLEMA PRINCIPAL: Endpoints WebSocket no encontrados")
            logger.info("   💡 Posibles causas:")
            logger.info("      - El WebSocket no está configurado en el servidor")
            logger.info("      - Ruta incorrecta del endpoint")
            logger.info("      - Problema de configuración en Render")
            
        # Verificar si hay conexión HTTP básica
        http_success = any(r["success"] for r in self.results if "HTTP" in r["test"])
        
        if http_success:
            logger.info("   ✅ Conectividad HTTP: Funcionando")
        else:
            logger.info("   🚨 Conectividad HTTP: Problema de conectividad básica")
        
        logger.info(f"\n📋 Recomendaciones:")
        
        if not any(r["success"] for r in self.results if "WebSocket" in r["test"]):
            logger.info("   1. 🔧 Verificar que el WebSocket esté habilitado en el servidor")
            logger.info("   2. 📝 Revisar la configuración de Render")
            logger.info("   3. 🔍 Verificar logs del servidor para errores")
            logger.info("   4. 📞 Contactar soporte de Render si es necesario")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "results": self.results
        }
    
    async def run_all_diagnostics(self):
        """Ejecuta todos los diagnósticos"""
        logger.info("🔬 INICIANDO DIAGNÓSTICO COMPLETO DEL WEBSOCKET")
        logger.info(f"🎯 URL objetivo: {self.base_url}")
        logger.info(f"🔐 Token configurado: {'Sí' if self.token else 'No'}")
        logger.info(f"⏰ Tiempo de inicio: {datetime.now().isoformat()}")
        
        try:
            await self.test_basic_http_connectivity()
            await self.test_health_check()
            await self.test_websocket_endpoint_discovery()
            await self.test_websocket_upgrade_headers()
            await self.test_websocket_libraries()
            await self.test_render_specific_issues()
            await self.test_alternative_protocols()
            
        except Exception as e:
            logger.error(f"❌ Error durante diagnósticos: {str(e)}")
            logger.error(traceback.format_exc())
        
        finally:
            summary = self.generate_diagnosis_report()
            logger.info(f"\n⏰ Tiempo de finalización: {datetime.now().isoformat()}")
            logger.info("🏁 DIAGNÓSTICO COMPLETADO")
            
            return summary

async def main():
    """Función principal"""
    diagnostic = WebSocketDiagnostic()
    
    try:
        summary = await diagnostic.run_all_diagnostics()
        
        # Determinar código de salida
        if summary["success_rate"] >= 50:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("\n⛔ Diagnóstico interrumpido por el usuario")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Error fatal: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    # Verificar dependencias
    try:
        import aiohttp
    except ImportError:
        print("❌ Error: aiohttp no está instalado")
        print("📦 Instálalo con: pip install aiohttp")
        sys.exit(1)
    
    print("🔬 DIAGNÓSTICO WEBSOCKET - FULLSTACKAGENT")
    print("=" * 50)
    print("🎯 Este script identificará problemas con el WebSocket")
    print("📍 URL objetivo: https://waagentv1.onrender.com")
    print("⏱️  Tiempo estimado: 1-2 minutos")
    print("=" * 50)
    
    asyncio.run(main())