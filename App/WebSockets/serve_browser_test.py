"""
Script para servir la interfaz de prueba de WebSockets en un navegador.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Puerto para el servidor HTTP
PORT = 8080

class BrowserTestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler personalizado para servir la interfaz de prueba."""
    
    def __init__(self, *args, **kwargs):
        # Obtener la ruta al directorio del módulo WebSockets
        module_dir = Path(__file__).parent
        
        # Cambiar al directorio del módulo WebSockets
        os.chdir(module_dir)
        
        # Inicializar el handler
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Sobrescribir el método de logging para usar nuestro logger."""
        logger.info("%s - %s" % (self.address_string(), format % args))

def main():
    """Función principal."""
    logger.info(f"Iniciando servidor HTTP en puerto {PORT}")
    
    # Crear servidor HTTP
    with socketserver.TCPServer(("", PORT), BrowserTestHandler) as httpd:
        # Mostrar URL
        url = f"http://localhost:{PORT}/browser_test.html"
        logger.info(f"Servidor iniciado en {url}")
        
        # Abrir navegador
        logger.info("Abriendo navegador...")
        webbrowser.open(url)
        
        # Servir hasta que se interrumpa con Ctrl+C
        try:
            logger.info("Presiona Ctrl+C para detener el servidor")
            httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info("Servidor detenido")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
