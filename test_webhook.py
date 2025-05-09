import requests
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
WEBHOOK_URL = input("Ingresa la URL del webhook (ej: https://tu-app.onrender.com/webhook): ")
WHATSAPP_WEBHOOK_TOKEN = os.getenv("WHATSAPP_WEBHOOK_TOKEN")

def test_webhook_verification():
    """
    Prueba la verificación del webhook simulando la solicitud de Meta.
    """
    # Construir URL con parámetros de verificación
    challenge = "123456789"
    verification_url = f"{WEBHOOK_URL}?hub.mode=subscribe&hub.challenge={challenge}&hub.verify_token={WHATSAPP_WEBHOOK_TOKEN}"
    
    print(f"Enviando solicitud de verificación a: {verification_url}")
    
    # Enviar solicitud GET para verificación
    response = requests.get(verification_url)
    
    print(f"Código de respuesta: {response.status_code}")
    print(f"Respuesta: {response.text}")
    
    if response.status_code == 200 and response.text == challenge:
        print("\n✅ Verificación exitosa! El webhook está configurado correctamente.")
    else:
        print("\n❌ Error en la verificación. Verifica el token y la URL del webhook.")

def test_webhook_message():
    """
    Prueba el envío de un mensaje simulado al webhook.
    """
    # Construir payload simulando un mensaje de WhatsApp
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "1234567890",
                                "phone_number_id": "1234567890"
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Test User"
                                    },
                                    "wa_id": "573001234567"
                                }
                            ],
                            "messages": [
                                {
                                    "from": "573001234567",
                                    "id": "wamid.test123456789",
                                    "timestamp": "1683123456",
                                    "text": {
                                        "body": "Mensaje de prueba desde test_webhook.py"
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    # Calcular firma (en un entorno real, Meta firma los webhooks)
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Enviando mensaje simulado a: {WEBHOOK_URL}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Enviar solicitud POST con el mensaje simulado
    response = requests.post(WEBHOOK_URL, headers=headers, json=payload)
    
    print(f"Código de respuesta: {response.status_code}")
    print(f"Respuesta: {response.text}")
    
    if response.status_code == 200:
        print("\n✅ Mensaje enviado exitosamente al webhook!")
    else:
        print("\n❌ Error al enviar el mensaje al webhook.")

if __name__ == "__main__":
    print("=== Test de Webhook de WhatsApp ===\n")
    
    # Menú de opciones
    print("Selecciona una opción:")
    print("1. Probar verificación del webhook")
    print("2. Probar envío de mensaje al webhook")
    print("3. Ejecutar ambas pruebas")
    
    option = input("\nOpción (1-3): ")
    
    if option == "1":
        test_webhook_verification()
    elif option == "2":
        test_webhook_message()
    elif option == "3":
        test_webhook_verification()
        print("\n" + "-"*50 + "\n")
        test_webhook_message()
    else:
        print("Opción no válida.")
