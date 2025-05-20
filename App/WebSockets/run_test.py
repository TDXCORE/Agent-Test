"""
Script para ejecutar el servidor y cliente de prueba en paralelo.
"""

import asyncio
import logging
import sys
import os
import subprocess
import time
import signal
import threading

# Añadir directorio raíz al path para poder importar App
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_server():
    """Ejecuta el servidor de prueba."""
    logger.info("Iniciando servidor de prueba...")
    
    # Ejecutar el servidor en un proceso separado
    server_process = subprocess.Popen(
        [sys.executable, "-m", "App.WebSockets.test_server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Leer la salida del servidor en tiempo real
    def read_output():
        for line in server_process.stdout:
            print(f"[SERVER] {line.strip()}")
    
    # Leer errores del servidor en tiempo real
    def read_errors():
        for line in server_process.stderr:
            print(f"[SERVER ERROR] {line.strip()}")
    
    # Iniciar hilos para leer la salida y errores
    threading.Thread(target=read_output, daemon=True).start()
    threading.Thread(target=read_errors, daemon=True).start()
    
    return server_process

def run_client():
    """Ejecuta el cliente de prueba."""
    logger.info("Esperando a que el servidor esté listo...")
    
    # Esperar a que el servidor esté listo (5 segundos)
    time.sleep(5)
    
    logger.info("Iniciando cliente de prueba...")
    
    # Ejecutar el cliente en un proceso separado
    client_process = subprocess.Popen(
        [sys.executable, "-m", "App.WebSockets.simple_test"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Leer la salida del cliente en tiempo real
    def read_output():
        for line in client_process.stdout:
            print(f"[CLIENT] {line.strip()}")
    
    # Leer errores del cliente en tiempo real
    def read_errors():
        for line in client_process.stderr:
            print(f"[CLIENT ERROR] {line.strip()}")
    
    # Iniciar hilos para leer la salida y errores
    threading.Thread(target=read_output, daemon=True).start()
    threading.Thread(target=read_errors, daemon=True).start()
    
    return client_process

def main():
    """Función principal."""
    logger.info("Iniciando prueba completa de WebSockets")
    
    try:
        # Iniciar servidor
        server_process = run_server()
        
        # Iniciar cliente
        client_process = run_client()
        
        # Esperar a que el cliente termine
        client_process.wait()
        
        # Verificar resultado del cliente
        if client_process.returncode == 0:
            logger.info("Prueba completada exitosamente")
        else:
            logger.error(f"Prueba fallida con código de salida {client_process.returncode}")
        
        # Terminar servidor
        logger.info("Terminando servidor...")
        server_process.send_signal(signal.SIGTERM)
        server_process.wait(timeout=5)
    
    except KeyboardInterrupt:
        logger.info("Prueba interrumpida por el usuario")
    
    except Exception as e:
        logger.error(f"Error durante la prueba: {str(e)}")
    
    finally:
        # Asegurar que todos los procesos terminen
        try:
            if 'server_process' in locals() and server_process.poll() is None:
                server_process.terminate()
                server_process.wait(timeout=2)
        except:
            pass
        
        try:
            if 'client_process' in locals() and client_process.poll() is None:
                client_process.terminate()
                client_process.wait(timeout=2)
        except:
            pass
    
    logger.info("Prueba finalizada")

if __name__ == "__main__":
    main()
