# Despliegue en Render

Este documento proporciona instrucciones para desplegar la aplicación en Render.

## Requisitos previos

1. Cuenta en [Render](https://render.com/)
2. Repositorio Git con el código de la aplicación
3. Variables de entorno configuradas (ver sección "Variables de entorno")

## Pasos para el despliegue

### 1. Despliegue inicial con aplicación simplificada

Para evitar problemas con dependencias complejas durante el despliegue inicial, se recomienda comenzar con la aplicación simplificada:

1. Inicia sesión en tu cuenta de Render
2. Haz clic en "New" y selecciona "Web Service"
3. Conecta tu repositorio Git
4. Configura el servicio:
   - **Nombre**: Elige un nombre para tu servicio (ej. whatsapp-webhook)
   - **Entorno**: Python
   - **Región**: Selecciona la región más cercana a tus usuarios
   - **Rama**: main (o la rama que desees desplegar)
   - **Comando de construcción**: `pip install -r requirements.txt`
   - **Comando de inicio**: `gunicorn simple_app:app --timeout 120`

### 2. Migración a la aplicación completa

Una vez que el despliegue inicial sea exitoso y hayas configurado todas las variables de entorno correctamente, puedes migrar a la aplicación completa:

1. Ve a la sección "Settings" de tu servicio en Render
2. Actualiza el comando de inicio a: `gunicorn whatsapp_api:app --timeout 120`
3. Haz clic en "Save Changes"
4. Inicia un nuevo despliegue desde la sección "Manual Deploy"

### 2. Configurar variables de entorno

En la sección "Environment" de tu servicio en Render, añade las siguientes variables de entorno:

```
OPENAI_API_KEY=tu_clave_api_openai
LANGCHAIN_API_KEY=tu_clave_api_langchain
LANGSMITH_PROJECT=tu_proyecto_langsmith

AZURE_TENANT_ID=tu_tenant_id
AZURE_CLIENT_ID=tu_client_id
AZURE_CLIENT_SECRET=tu_client_secret
USER_EMAIL=tu_email@ejemplo.com
TIMEZONE=America/Bogota

WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id
WHATSAPP_ACCESS_TOKEN=tu_access_token
WHATSAPP_WEBHOOK_TOKEN=tu_webhook_verification_token
WHATSAPP_APP_SECRET=tu_app_secret

NEXT_PUBLIC_SUPABASE_URL=tu_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=tu_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=tu_supabase_service_role_key
```

### 3. Desplegar el servicio

1. Haz clic en "Create Web Service"
2. Render comenzará a construir y desplegar tu aplicación
3. Una vez completado, Render te proporcionará una URL pública (ej. https://whatsapp-webhook.onrender.com)

## Configuración de WhatsApp Business API

### 1. Configurar el webhook en Meta for Developers

1. Inicia sesión en [Meta for Developers](https://developers.facebook.com/)
2. Ve a tu aplicación de WhatsApp Business
3. En la sección "Webhooks", configura:
   - **URL de callback**: `https://tu-app.onrender.com/webhook`
   - **Token de verificación**: El mismo valor que configuraste en `WHATSAPP_WEBHOOK_TOKEN`
   - **Campos a suscribir**: messages, message_deliveries, messaging_postbacks

### 2. Verificar la integración

1. Envía un mensaje a tu número de WhatsApp Business
2. Verifica que tu aplicación reciba el webhook (puedes ver los logs en Render)
3. Verifica que tu aplicación responda correctamente al mensaje

## Solución de problemas

### Error de despliegue

Si encuentras errores durante el despliegue, verifica:

1. Que el archivo `requirements.txt` esté correctamente formateado
2. Que todas las variables de entorno estén configuradas
3. Que el comando de inicio sea correcto
4. Que no exista el archivo `supabase.py` (debe usar `supabase_client.py` en su lugar para evitar importaciones circulares)

### Error de webhook

Si WhatsApp no puede verificar tu webhook, verifica:

1. Que la URL sea accesible públicamente
2. Que el token de verificación coincida
3. Que la ruta `/webhook` esté correctamente implementada en tu aplicación

### Error de API de WhatsApp

Si no puedes enviar mensajes a través de la API de WhatsApp, verifica:

1. Que `WHATSAPP_PHONE_NUMBER_ID` y `WHATSAPP_ACCESS_TOKEN` sean correctos
2. Que tu número de WhatsApp Business esté correctamente configurado
3. Que tengas los permisos necesarios para enviar mensajes

## Recursos adicionales

- [Documentación de Render](https://render.com/docs)
- [Documentación de WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Documentación de Flask](https://flask.palletsprojects.com/)
