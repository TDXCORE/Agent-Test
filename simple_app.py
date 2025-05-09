from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
WHATSAPP_WEBHOOK_TOKEN = os.getenv("WHATSAPP_WEBHOOK_TOKEN", "default_token")

# Inicializar Flask
app = Flask(__name__)

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """
    Maneja la verificación del webhook por parte de WhatsApp.
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == WHATSAPP_WEBHOOK_TOKEN:
        print("Webhook verificado!")
        return challenge, 200
    else:
        print(f"Verificación fallida. Mode: {mode}, Token recibido: {token}, Token esperado: {WHATSAPP_WEBHOOK_TOKEN}")
        return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def receive_webhook():
    """
    Recibe notificaciones de mensajes y eventos de WhatsApp.
    """
    # Simplemente responder OK para la validación
    return "OK", 200

@app.route('/')
def index():
    return "Webhook simplificado para validación de Meta. Usa /webhook para la verificación."

# Punto de entrada para Render
if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
