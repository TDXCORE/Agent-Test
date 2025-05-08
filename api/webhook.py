import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Configuración
WHATSAPP_WEBHOOK_TOKEN = os.environ.get("WHATSAPP_WEBHOOK_TOKEN")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Maneja la verificación del webhook por parte de WhatsApp."""
        # Parsear la URL y los parámetros de consulta
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        # Obtener los parámetros del desafío
        mode = query_params.get('hub.mode', [''])[0]
        token = query_params.get('hub.verify_token', [''])[0]
        challenge = query_params.get('hub.challenge', [''])[0]
        
        # Verificar el token
        if mode == 'subscribe' and token == WHATSAPP_WEBHOOK_TOKEN:
            # Responder con el desafío
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(challenge.encode())
            print(f"Webhook verificado! Challenge: {challenge}")
        else:
            # Responder con error
            self.send_response(403)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write("Verification failed".encode())
            print(f"Verificación fallida. Mode: {mode}, Token recibido: {token}, Token esperado: {WHATSAPP_WEBHOOK_TOKEN}")
    
    def do_POST(self):
        """Recibe notificaciones de mensajes y eventos de WhatsApp."""
        # Simplemente responder OK para la validación
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write("OK".encode())
