import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Configuración
WHATSAPP_WEBHOOK_TOKEN = os.environ.get("WHATSAPP_WEBHOOK_TOKEN")

def handler(request, context):
    """
    Maneja las solicitudes al webhook de WhatsApp.
    
    Args:
        request: Objeto de solicitud HTTP
        context: Contexto de la función
        
    Returns:
        Respuesta HTTP
    """
    # Determinar el método HTTP
    if request.method == "GET":
        # Manejar verificación del webhook
        query_params = request.query
        
        # Obtener los parámetros del desafío
        mode = query_params.get('hub.mode', [''])[0] if 'hub.mode' in query_params else ''
        token = query_params.get('hub.verify_token', [''])[0] if 'hub.verify_token' in query_params else ''
        challenge = query_params.get('hub.challenge', [''])[0] if 'hub.challenge' in query_params else ''
        
        print(f"Verificando webhook. Mode: {mode}, Token: {token}, Challenge: {challenge}")
        print(f"Token esperado: {WHATSAPP_WEBHOOK_TOKEN}")
        
        # Verificar el token
        if mode == 'subscribe' and token == WHATSAPP_WEBHOOK_TOKEN:
            # Responder con el desafío
            print("Webhook verificado!")
            return {
                "statusCode": 200,
                "body": challenge
            }
        else:
            # Responder con error
            print(f"Verificación fallida. Mode: {mode}, Token recibido: {token}, Token esperado: {WHATSAPP_WEBHOOK_TOKEN}")
            return {
                "statusCode": 403,
                "body": "Verification failed"
            }
    
    elif request.method == "POST":
        # Manejar notificaciones de mensajes
        return {
            "statusCode": 200,
            "body": "OK"
        }
    
    else:
        # Método no soportado
        return {
            "statusCode": 405,
            "body": "Method not allowed"
        }
