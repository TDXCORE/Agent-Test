from flask import Flask, request, jsonify
import requests
import json
import hmac
import hashlib
import os
import time
from dotenv import load_dotenv
import logging
from concurrent.futures import ThreadPoolExecutor

# Importar el agente de main.py
from main import create_lead_qualification_agent
# Importar operaciones de base de datos
from db_operations import (
    get_or_create_user,
    get_or_create_conversation,
    add_message,
    get_conversation_history
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de WhatsApp
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_WEBHOOK_TOKEN = os.getenv("WHATSAPP_WEBHOOK_TOKEN")
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET")

# Configuración de timeouts (60 segundos)
REQUEST_TIMEOUT = 60

# Inicializar Flask
app = Flask(__name__)

# Inicializar el agente
lead_agent = create_lead_qualification_agent()

# Inicializar ThreadPoolExecutor para manejar múltiples conversaciones
executor = ThreadPoolExecutor(max_workers=10)

# ---- CLIENTE DE WHATSAPP ----

def send_whatsapp_message(to, message_type, content, caption=None):
    """
    Envía un mensaje a WhatsApp usando la Cloud API.
    
    Args:
        to: Número de teléfono del destinatario
        message_type: Tipo de mensaje (text, image, audio, video)
        content: Contenido del mensaje (texto o URL)
        caption: Pie de foto/video (opcional)
    
    Returns:
        Respuesta de la API
    """
    start_time = time.time()
    logger.info(f"Enviando mensaje a {to} (tipo: {message_type})")
    
    api_version = "v17.0"
    url = f"https://graph.facebook.com/{api_version}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Construir payload según el tipo de mensaje
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to
    }
    
    if message_type == "text":
        payload["type"] = "text"
        payload["text"] = {"body": content}
    
    elif message_type == "image":
        payload["type"] = "image"
        payload["image"] = {"link": content}
        if caption:
            payload["image"]["caption"] = caption
    
    elif message_type == "audio":
        payload["type"] = "audio"
        payload["audio"] = {"link": content}
    
    elif message_type == "video":
        payload["type"] = "video"
        payload["video"] = {"link": content}
        if caption:
            payload["video"]["caption"] = caption
    
    # Enviar solicitud a la API con timeout
    try:
        response = requests.post(
            url, 
            headers=headers, 
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Respuesta recibida en {elapsed_time:.2f}s (status: {response.status_code})")
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error al enviar mensaje: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al enviar mensaje a {to} después de {REQUEST_TIMEOUT}s")
        return None
    except Exception as e:
        logger.error(f"Error al enviar mensaje: {str(e)}")
        return None

def mark_message_as_read(message_id):
    """Marca un mensaje como leído"""
    api_version = "v17.0"
    url = f"https://graph.facebook.com/{api_version}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id
    }
    
    try:
        response = requests.post(
            url, 
            headers=headers, 
            json=payload,
            timeout=REQUEST_TIMEOUT
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error al marcar mensaje como leído: {str(e)}")
        return False

def get_media_url(media_id):
    """Obtiene la URL de un archivo multimedia"""
    api_version = "v17.0"
    url = f"https://graph.facebook.com/{api_version}/{media_id}"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }
    
    try:
        response = requests.get(
            url, 
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            media_data = response.json()
            media_url = media_data.get("url")
            
            if media_url:
                media_response = requests.get(
                    media_url,
                    headers={"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"},
                    timeout=REQUEST_TIMEOUT
                )
                if media_response.status_code == 200:
                    return media_response.content
        
        return None
    except Exception as e:
        logger.error(f"Error al obtener URL de multimedia: {str(e)}")
        return None

# ---- PROCESAMIENTO DE MENSAJES ----

def process_incoming_message(sender, message_type, content, message_id=None):
    """
    Procesa los mensajes entrantes usando el agente de calificación de leads.
    """
    start_time = time.time()
    logger.info(f"Procesando mensaje de {sender} (tipo: {message_type})")
    
    try:
        # Marcar mensaje como leído si tenemos el ID
        if message_id:
            mark_message_as_read(message_id)
        
        # Obtener o crear usuario
        user = get_or_create_user(phone=sender)
        
        # Obtener o crear conversación
        conversation = get_or_create_conversation(user_id=user["id"], external_id=sender, platform="whatsapp")
        
        # Preparar el contenido del mensaje según el tipo
        message_content = content
        if message_type != "text":
            # Para mensajes multimedia, informamos al agente del tipo de contenido
            media_type_names = {
                "image": "imagen",
                "audio": "audio",
                "video": "video"
            }
            message_content = f"[El usuario ha enviado un archivo de tipo {media_type_names.get(message_type, 'multimedia')}]"
        
        # Agregar mensaje del usuario a la base de datos
        add_message(
            conversation_id=conversation["id"],
            role="user",
            content=message_content,
            message_type=message_type,
            external_id=message_id
        )
        
        # Obtener historial de mensajes para el agente
        messages_history = get_conversation_history(conversation["id"])
        
        # Si es una nueva conversación, agregar mensaje de sistema
        if len(messages_history) == 0:
            # Agregar mensaje de sistema
            add_message(
                conversation_id=conversation["id"],
                role="system",
                content="Iniciando conversación con un potencial cliente."
            )
            
            # Agregar mensaje de bienvenida
            add_message(
                conversation_id=conversation["id"],
                role="assistant",
                content="¡Hola! Soy el asistente virtual de nuestra empresa de desarrollo de software. ¿En qué puedo ayudarte hoy?"
            )
            
            # Actualizar historial
            messages_history = get_conversation_history(conversation["id"])
        
        # Configuración para la ejecución del agente
        config = {
            "configurable": {
                "thread_id": sender
            }
        }
        
        # Invocar al agente con el historial de mensajes
        response = lead_agent.invoke(
            {"messages": messages_history},
            config
        )
        
        # Obtener la respuesta del agente
        assistant_message = response["messages"][-1]
        if hasattr(assistant_message, "content"):
            # Si es un objeto de mensaje de LangChain
            agent_response = assistant_message.content
        elif isinstance(assistant_message, dict) and "content" in assistant_message:
            # Si es un diccionario
            agent_response = assistant_message["content"]
        else:
            # Fallback
            agent_response = str(assistant_message)
        
        # Enviar la respuesta al usuario
        send_whatsapp_message(sender, "text", agent_response)
        
        # Guardar respuesta del asistente en la base de datos
        add_message(
            conversation_id=conversation["id"],
            role="assistant",
            content=agent_response,
            message_type="text"
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Mensaje procesado en {elapsed_time:.2f}s")
        
        return True
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error al procesar mensaje después de {elapsed_time:.2f}s: {str(e)}")
        
        # Enviar mensaje de error al usuario
        error_message = "Lo siento, estamos experimentando dificultades técnicas. Por favor, intenta nuevamente más tarde."
        send_whatsapp_message(sender, "text", error_message)
        return False

# ---- RUTAS DEL WEBHOOK ----

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """
    Maneja la verificación del webhook por parte de WhatsApp.
    """
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode == 'subscribe' and token == WHATSAPP_WEBHOOK_TOKEN:
        logger.info("Webhook verificado!")
        return challenge, 200
    else:
        logger.warning(f"Verificación fallida. Mode: {mode}, Token recibido: {token}, Token esperado: {WHATSAPP_WEBHOOK_TOKEN}")
        return "Verification failed", 403

@app.route('/webhook', methods=['POST'])
def receive_webhook():
    """
    Recibe notificaciones de mensajes y eventos de WhatsApp.
    """
    # Verificar firma X-Hub-Signature-256
    signature = request.headers.get('X-Hub-Signature-256', '')
    
    if WHATSAPP_APP_SECRET:
        payload = request.data
        expected_signature = 'sha256=' + hmac.new(
            WHATSAPP_APP_SECRET.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning("Firma inválida en webhook")
            return "Invalid signature", 403
    
    # Procesar datos del webhook
    data = request.json
    logger.info(f"Webhook recibido: {json.dumps(data)[:200]}...")
    
    # Verificar si es un mensaje entrante
    if data.get('object') == 'whatsapp_business_account':
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                if change.get('field') == 'messages':
                    # Procesar mensajes en un hilo separado para no bloquear la respuesta
                    executor.submit(process_webhook_messages, change.get('value', {}))
    
    # Responder rápidamente para cumplir con el requisito de WhatsApp
    return "OK", 200

def process_webhook_messages(message_data):
    """
    Procesa los mensajes recibidos en el webhook.
    """
    messages = message_data.get('messages', [])
    for message in messages:
        message_type = message.get('type')
        sender = message.get('from')
        message_id = message.get('id')
        
        if message_type == 'text':
            text = message.get('text', {}).get('body', '')
            process_incoming_message(sender, 'text', text, message_id)
        
        elif message_type in ["image", "audio", "video"]:
            media_id = message.get(message_type, {}).get('id')
            # Para mensajes multimedia, informamos al agente del tipo de contenido
            media_type_names = {
                "image": "imagen",
                "audio": "audio",
                "video": "video"
            }
            media_message = f"[El usuario ha enviado un archivo de tipo {media_type_names.get(message_type, 'multimedia')}]"
            process_incoming_message(sender, 'text', media_message, message_id)

# ---- SERVIDOR PARA DESARROLLO LOCAL ----

@app.route('/')
def index():
    return "WhatsApp Webhook está funcionando. Usa /webhook para recibir mensajes."

# Punto de entrada para Vercel
handler = app

# Ejecutar servidor local si se ejecuta directamente
if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
