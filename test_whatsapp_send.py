import requests
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de WhatsApp
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")

def send_whatsapp_message(to, message):
    """
    Envía un mensaje de texto a WhatsApp usando la Cloud API.
    
    Args:
        to: Número de teléfono del destinatario (con código de país, sin + o 00)
        message: Contenido del mensaje
    
    Returns:
        Respuesta de la API
    """
    api_version = "v17.0"
    url = f"https://graph.facebook.com/{api_version}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    
    print(f"Enviando mensaje a {to}: {message}")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Enviar solicitud a la API
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
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
    
    # Solicitar mensaje al usuario
    message = input("Ingresa el mensaje a enviar: ")
    
    # Enviar mensaje
    result = send_whatsapp_message(to, message)
    
    if result:
        print("\n¡Mensaje enviado exitosamente!")
        print(f"ID del mensaje: {result.get('messages', [{}])[0].get('id', 'No disponible')}")
    else:
        print("\nError al enviar el mensaje. Verifica las credenciales y el número de teléfono.")
