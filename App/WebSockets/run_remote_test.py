"""
Script para ejecutar pruebas de WebSocket en el servidor remoto.
Este script es un wrapper amigable para remote_websocket_test.py.
"""

import os
import sys
import subprocess
import argparse
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

def main():
    """Función principal."""
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description="Ejecutar pruebas de WebSocket en servidor remoto")
    parser.add_argument("--url", default="waagentv1.onrender.com", help="URL base del servidor (sin protocolo)")
    parser.add_argument("--token", default=WEBSOCKET_AUTH_TOKEN, help="Token de autenticación (opcional, por defecto usa WEBSOCKET_AUTH_TOKEN)")
    parser.add_argument("--insecure", action="store_true", help="Usar conexión no segura (ws:// en lugar de wss://)")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout en segundos para operaciones")
    parser.add_argument("--debug", action="store_true", help="Activar modo debug")
    
    args = parser.parse_args()
    
    # Construir comando para ejecutar remote_websocket_test.py
    cmd = [sys.executable, "-m", "App.WebSockets.remote_websocket_test"]
    
    # Añadir argumentos
    if args.url:
        cmd.extend(["--url", args.url])
    
    if args.token:
        cmd.extend(["--token", args.token])
    
    if args.insecure:
        cmd.append("--insecure")
    
    if args.timeout:
        cmd.extend(["--timeout", str(args.timeout)])
    
    if args.debug:
        cmd.append("--debug")
    
    # Mostrar comando
    print(f"Ejecutando: {' '.join(cmd)}")
    print("\nIniciando pruebas de WebSocket en servidor remoto...")
    print("="*80)
    
    # Ejecutar comando
    try:
        # Usar subprocess.run para ejecutar el comando y capturar la salida
        result = subprocess.run(cmd, check=True)
        
        # Si llegamos aquí, el comando se ejecutó correctamente
        print("\n" + "="*80)
        print("Pruebas completadas exitosamente.")
        
    except subprocess.CalledProcessError as e:
        # Si hay un error en el comando
        print("\n" + "="*80)
        print(f"Error al ejecutar las pruebas: {str(e)}")
        sys.exit(1)
    
    except KeyboardInterrupt:
        # Si el usuario interrumpe la ejecución
        print("\n" + "="*80)
        print("Pruebas interrumpidas por el usuario.")
        sys.exit(1)

if __name__ == "__main__":
    main()
