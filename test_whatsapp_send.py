import requests
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de WhatsApp
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")

# Variables adicionales de Postman (si no están en .env, usar valores por defecto)
BUSINESS_ID = "747682971423654"  # Business-ID de Postman
WABA_ID = "648404611299992"      # WABA-ID de Postman

def send_whatsapp_message(to, message="Hola, este es un mensaje de prueba."):
    """
    Envía un mensaje de texto a WhatsApp usando la Cloud API.
    
    Args:
        to: Número de teléfono del destinatario (con código de país, sin + o 00)
        message: Mensaje de texto a enviar (por defecto es un mensaje de prueba)
    
    Returns:
        Respuesta de la API
    """
    api_version = "v17.0"
    url = f"https://graph.facebook.com/{api_version}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Payload para mensaje de texto (no usa plantilla)
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {
            "body": message
        }
    }
    
    print(f"Enviando mensaje de texto a {to}")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    # Enviar solicitud a la API
    response = requests.post(url, headers=headers, json=payload)
    
    print(f"Código de respuesta: {response.status_code}")
    print(f"Respuesta: {response.text}")
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")
        return None

if __name__ == "__main__":
    # Solicitar número de teléfono al usuario
    to = input("Ingresa el número de teléfono del destinatario (con código de país, sin + o 00, ej: 573001234567): ")
    
    # Solicitar mensaje personalizado (opcional)
    use_custom = input("¿Deseas enviar un mensaje personalizado? (s/n): ").lower() == 's'
    message = input("Escribe tu mensaje: ") if use_custom else "Hola, este es un mensaje de prueba."
    
    # Enviar mensaje de texto
    result = send_whatsapp_message(to, message)
    
    if result:
        print("\n¡Mensaje de texto enviado exitosamente!")
        print(f"ID del mensaje: {result.get('messages', [{}])[0].get('id', 'No disponible')}")
    else:
        print("\nError al enviar el mensaje. Verifica las credenciales y el número de teléfono.")
