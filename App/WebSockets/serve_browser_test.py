"""
Script para servir el archivo browser_test.html localmente.
Inicia un servidor web simple para acceder a la interfaz de prueba de WebSockets.
"""

import http.server
import socketserver
import os
import webbrowser
import argparse
import sys

# Añadir directorio raíz al path para poder importar App
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def main():
    """Función principal."""
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description="Servir la interfaz de prueba de WebSockets")
    parser.add_argument("--port", type=int, default=8080, help="Puerto para el servidor web (por defecto: 8080)")
    parser.add_argument("--no-browser", action="store_true", help="No abrir automáticamente el navegador")
    
    args = parser.parse_args()
    
    # Obtener directorio actual
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Verificar que el archivo existe
    html_file = os.path.join(current_dir, "browser_test.html")
    if not os.path.exists(html_file):
        print(f"Error: No se encontró el archivo {html_file}")
        sys.exit(1)
    
    # Cambiar al directorio del script
    os.chdir(current_dir)
    
    # Configurar y iniciar servidor
    port = args.port
    handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            url = f"http://localhost:{port}/browser_test.html"
            
            print(f"Servidor iniciado en {url}")
            print("Presiona Ctrl+C para detener el servidor")
            
            # Abrir navegador automáticamente
            if not args.no_browser:
                print(f"Abriendo navegador en {url}")
                webbrowser.open(url)
            
            # Iniciar servidor
            httpd.serve_forever()
    
    except KeyboardInterrupt:
        print("\nServidor detenido")
    
    except OSError as e:
        if e.errno == 98:  # Address already in use
            print(f"Error: El puerto {port} ya está en uso. Intenta con otro puerto:")
            print(f"python -m App.WebSockets.serve_browser_test --port {port+1}")
        else:
            print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
