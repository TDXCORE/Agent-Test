"""
Script para ejecutar el servidor local y probar la conexión WebSocket.
"""

import subprocess
import sys
import os
import time
import signal
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_server():
    """Ejecuta el servidor FastAPI en un proceso separado."""
    logger.info("Iniciando servidor FastAPI...")
    
    # Obtener la ruta al directorio raíz del proyecto
    root_dir = Path(__file__).parent.parent.parent
    
    # Comando para ejecutar el servidor
    cmd = [sys.executable, "-m", "uvicorn", "App.api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    
    # Ejecutar el servidor en un proceso separado
    server_process = subprocess.Popen(
        cmd,
        cwd=root_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    logger.info(f"Servidor iniciado con PID {server_process.pid}")
    return server_process

def run_test():
    """Ejecuta el script de prueba WebSocket."""
    logger.info("Ejecutando prueba WebSocket...")
    
    # Obtener la ruta al directorio raíz del proyecto
    root_dir = Path(__file__).parent.parent.parent
    
    # Comando para ejecutar la prueba
    cmd = [sys.executable, "-m", "App.WebSockets.local_test"]
    
    # Ejecutar la prueba en un proceso separado
    test_process = subprocess.Popen(
        cmd,
        cwd=root_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    # Capturar la salida de la prueba
    stdout, stderr = test_process.communicate()
    
    # Mostrar la salida
    logger.info("=== SALIDA DE LA PRUEBA ===")
    logger.info(stdout)
    
    if stderr:
        logger.error("=== ERRORES DE LA PRUEBA ===")
        logger.error(stderr)
    
    return test_process.returncode == 0

def main():
    """Función principal."""
    logger.info("Iniciando prueba de integración WebSocket")
    
    # Iniciar el servidor
    server_process = run_server()
    
    try:
        # Esperar a que el servidor esté listo
        logger.info("Esperando a que el servidor esté listo...")
        time.sleep(5)
        
        # Ejecutar la prueba
        success = run_test()
        
        if success:
            logger.info("✅ Prueba de integración exitosa")
        else:
            logger.error("❌ Prueba de integración fallida")
        
    finally:
        # Detener el servidor
        logger.info(f"Deteniendo servidor (PID {server_process.pid})...")
        
        # En Windows, usar taskkill para matar el proceso
        if os.name == 'nt':
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(server_process.pid)], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # En Unix, usar señal SIGTERM
        else:
            server_process.send_signal(signal.SIGTERM)
            server_process.wait(timeout=5)
        
        logger.info("Servidor detenido")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
