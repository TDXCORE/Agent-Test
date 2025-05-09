import requests
import json
import os
from dotenv import load_dotenv
import sys

# Cargar variables de entorno
load_dotenv()

# Configuración de WhatsApp
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_WEBHOOK_TOKEN = os.getenv("WHATSAPP_WEBHOOK_TOKEN")

# URL base de la aplicación desplegada
APP_URL = os.getenv("APP_URL", "https://whatsapp-webhook.onrender.com")

def check_webhook_status():
    """
    Verifica el estado del webhook haciendo una solicitud GET a la ruta /webhook
    """
    print("\n=== Verificando estado del webhook ===")
    
    # Construir URL con parámetros de verificación
    url = f"{APP_URL}/webhook?hub.mode=subscribe&hub.verify_token={WHATSAPP_WEBHOOK_TOKEN}&hub.challenge=challenge_token"
    
    try:
        response = requests.get(url)
        print(f"Código de respuesta: {response.status_code}")
        print(f"Respuesta: {response.text}")
        
        if response.status_code == 200 and response.text == "challenge_token":
            print("✅ El webhook está correctamente configurado y responde a la verificación")
        else:
            print("❌ El webhook no está respondiendo correctamente a la verificación")
    except Exception as e:
        print(f"❌ Error al verificar el webhook: {str(e)}")

def check_whatsapp_api():
    """
    Verifica la conexión con la API de WhatsApp
    """
    print("\n=== Verificando conexión con la API de WhatsApp ===")
    
    if not WHATSAPP_PHONE_NUMBER_ID or not WHATSAPP_ACCESS_TOKEN:
        print("❌ Faltan variables de entorno para la API de WhatsApp")
        return
    
    api_version = "v17.0"
    url = f"https://graph.facebook.com/{api_version}/{WHATSAPP_PHONE_NUMBER_ID}"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Código de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Conexión exitosa con la API de WhatsApp")
            print(f"   ID del número: {data.get('id')}")
            print(f"   Nombre del número: {data.get('display_phone_number')}")
        else:
            print(f"❌ Error al conectar con la API de WhatsApp: {response.text}")
    except Exception as e:
        print(f"❌ Error al verificar la API de WhatsApp: {str(e)}")

def check_app_health():
    """
    Verifica la salud general de la aplicación
    """
    print("\n=== Verificando salud general de la aplicación ===")
    
    try:
        response = requests.get(f"{APP_URL}/")
        print(f"Código de respuesta: {response.status_code}")
        print(f"Respuesta: {response.text}")
        
        if response.status_code == 200:
            print("✅ La aplicación está en línea y respondiendo")
        else:
            print("❌ La aplicación no está respondiendo correctamente")
    except Exception as e:
        print(f"❌ Error al verificar la salud de la aplicación: {str(e)}")

def send_test_message():
    """
    Envía un mensaje de prueba para verificar la integración completa
    """
    print("\n=== Enviando mensaje de prueba ===")
    
    # Solicitar número de teléfono al usuario
    to = input("Ingresa el número de teléfono del destinatario (con código de país, sin + o 00, ej: 573001234567): ")
    
    api_version = "v17.0"
    url = f"https://graph.facebook.com/{api_version}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Payload para mensaje de texto
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {
            "body": "Este es un mensaje de prueba para verificar la integración completa."
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Código de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Mensaje enviado exitosamente")
            print(f"   ID del mensaje: {result.get('messages', [{}])[0].get('id', 'No disponible')}")
            print("\nAhora responde a este mensaje en WhatsApp y verifica que:")
            print("1. El webhook reciba la notificación (revisa los logs en Render)")
            print("2. El agente procese el mensaje (revisa los logs en Render y LangSmith)")
            print("3. Recibas una respuesta del agente en WhatsApp")
        else:
            print(f"❌ Error al enviar el mensaje: {response.text}")
    except Exception as e:
        print(f"❌ Error al enviar el mensaje de prueba: {str(e)}")

def main():
    print("=== Herramienta de diagnóstico para WhatsApp Webhook ===")
    print("Esta herramienta te ayudará a verificar el estado de la integración con WhatsApp")
    
    # Verificar que APP_URL esté configurado
    if not os.getenv("APP_URL"):
        app_url = input("Ingresa la URL base de tu aplicación (ej: https://whatsapp-webhook.onrender.com): ")
        os.environ["APP_URL"] = app_url
    
    while True:
        print("\nSelecciona una opción:")
        print("1. Verificar estado del webhook")
        print("2. Verificar conexión con la API de WhatsApp")
        print("3. Verificar salud general de la aplicación")
        print("4. Enviar mensaje de prueba")
        print("5. Ejecutar todas las verificaciones")
        print("6. Salir")
        
        option = input("\nOpción: ")
        
        if option == "1":
            check_webhook_status()
        elif option == "2":
            check_whatsapp_api()
        elif option == "3":
            check_app_health()
        elif option == "4":
            send_test_message()
        elif option == "5":
            check_app_health()
            check_webhook_status()
            check_whatsapp_api()
            send_test_message()
        elif option == "6":
            print("Saliendo...")
            sys.exit(0)
        else:
            print("Opción no válida. Intenta de nuevo.")
        
        input("\nPresiona Enter para continuar...")

if __name__ == "__main__":
    main()
