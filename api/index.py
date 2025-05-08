from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Maneja la solicitud a la ruta raíz."""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write("Webhook para WhatsApp Business API. Usa /api/webhook para la verificación.".encode())
