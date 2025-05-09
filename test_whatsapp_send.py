import requests
import json
import os
import sys
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de WhatsApp
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")

# Variables adicionales de Postman (si no están en .env, usar valores por defecto)
BUSINESS_ID = "747682971423654"  # Business-ID de Postman
WABA_ID = "648404611299992"      # WABA-ID de Postman

# Configuración de timeouts (30 segundos)
REQUEST_TIMEOUT = 30

def send_whatsapp_message(to, message="Hola, este es un mensaje de prueba."):
    """
    Envía un mensaje a WhatsApp usando la plantilla 'demo'.
    
    Args:
        to: Número de teléfono del destinatario (con código de país, sin + o 00)
        message: Mensaje de texto a enviar (no se usa con plantillas, pero se mantiene para compatibilidad)
    
    Returns:
        Respuesta de la API
    """
    start_time = time.time()
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Iniciando envío de mensaje con plantilla 'demo'")
    
    # Verificar que tenemos las credenciales necesarias
    if not WHATSAPP_PHONE_NUMBER_ID:
        print("ERROR: No se ha configurado WHATSAPP_PHONE_NUMBER_ID en el archivo .env")
        return None
    
    if not WHATSAPP_ACCESS_TOKEN:
        print("ERROR: No se ha configurado WHATSAPP_ACCESS_TOKEN en el archivo .env")
        return None
    
    api_version = "v17.0"
    url = f"https://graph.facebook.com/{api_version}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Payload para mensaje usando EXCLUSIVAMENTE la plantilla 'demo'
    # Esta es la única plantilla permitida según los requisitos
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": "demo",
            "language": {
                "code": "en"
            }
        }
    }
    
    print(f"Enviando mensaje con plantilla 'demo' a {to}")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps({k: '***' if k == 'Authorization' else v for k, v in headers.items()})}")
    print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    # Enviar solicitud a la API con timeout
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        
        elapsed_time = time.time() - start_time
        print(f"\nRespuesta recibida en {elapsed_time:.2f}s")
        print(f"Código de respuesta: {response.status_code}")
        print(f"Respuesta: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"ERROR: La API respondió con código {response.status_code}")
            print(f"Detalles: {response.text}")
            return None
    except requests.exceptions.Timeout:
        print(f"ERROR: Timeout al enviar mensaje después de {REQUEST_TIMEOUT}s")
        return None
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Error en la solicitud HTTP: {str(e)}")
        return None
    except Exception as e:
        print(f"ERROR: Error inesperado: {str(e)}")
        return None

if __name__ == "__main__":
    print("=== PRUEBA DE ENVÍO DE MENSAJE CON PLANTILLA 'DEMO' ===")
    print("NOTA: Solo se permite el uso de la plantilla 'demo' para esta prueba")
    
    # Solicitar número de teléfono al usuario o usar el proporcionado como argumento
    if len(sys.argv) > 1:
        to = sys.argv[1]
        print(f"Usando número de teléfono proporcionado como argumento: {to}")
    else:
        to = input("Ingresa el número de teléfono del destinatario (con código de país, sin + o 00, ej: 573001234567): ")
    
    # Validar formato básico del número
    if not to.isdigit():
        print("ERROR: El número de teléfono debe contener solo dígitos")
        sys.exit(1)
    
    # Enviar mensaje usando la plantilla 'demo'
    result = send_whatsapp_message(to)
    
    if result:
        print("\n¡ÉXITO! Mensaje con plantilla 'demo' enviado correctamente")
        print(f"ID del mensaje: {result.get('messages', [{}])[0].get('id', 'No disponible')}")
    else:
        print("\nERROR: No se pudo enviar el mensaje. Verifica las credenciales, la conexión a internet y el número de teléfono.")
