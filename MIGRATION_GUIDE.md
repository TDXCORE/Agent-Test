# Guía de Migración: De Simple App a WhatsApp API Completa

Esta guía proporciona los pasos para migrar de la aplicación simplificada (`simple_app.py`) a la implementación completa de la API de WhatsApp (`whatsapp_api.py`) en Render.

## Requisitos Previos

Antes de migrar a la implementación completa, asegúrate de que:

1. La aplicación simplificada está desplegada correctamente en Render
2. El webhook está verificado por Meta/WhatsApp (puedes usar `test_webhook.py` para comprobarlo)
3. Todas las variables de entorno están configuradas en Render

## Pasos para la Migración

### 1. Configurar Variables de Entorno

Asegúrate de que todas estas variables de entorno estén configuradas en Render:

```
# API Keys
OPENAI_API_KEY=tu_clave_api_openai
LANGCHAIN_API_KEY=tu_clave_api_langchain
LANGSMITH_PROJECT=tu_proyecto_langsmith

# Azure AD Credentials
AZURE_TENANT_ID=tu_tenant_id
AZURE_CLIENT_ID=tu_client_id
AZURE_CLIENT_SECRET=tu_client_secret
USER_EMAIL=tu_email@ejemplo.com
TIMEZONE=America/Bogota

# WhatsApp Business API
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id
WHATSAPP_ACCESS_TOKEN=tu_access_token
WHATSAPP_WEBHOOK_TOKEN=tu_webhook_verification_token
WHATSAPP_APP_SECRET=tu_app_secret

# Supabase
NEXT_PUBLIC_SUPABASE_URL=tu_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=tu_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=tu_supabase_service_role_key
```

### 2. Actualizar el Comando de Inicio

1. Ve a la sección "Settings" de tu servicio en Render
2. Busca la configuración "Start Command"
3. Cambia el comando de:
   ```
   gunicorn simple_app:app --timeout 120
   ```
   a:
   ```
   gunicorn whatsapp_api:app --timeout 120
   ```
4. Haz clic en "Save Changes"

### 3. Desplegar la Nueva Versión

1. Ve a la sección "Manual Deploy" de tu servicio en Render
2. Selecciona "Clear build cache & deploy"
3. Espera a que se complete el despliegue
4. Verifica los logs para asegurarte de que no hay errores

### 4. Verificar la Implementación Completa

1. Usa `test_webhook.py` para verificar que el webhook sigue funcionando correctamente
2. Usa `test_whatsapp_send.py` para enviar un mensaje de prueba
3. Envía un mensaje al número de WhatsApp Business desde tu teléfono y verifica que recibas una respuesta

## Solución de Problemas

### Error de Importación Circular

Si encuentras errores relacionados con importaciones circulares:

1. Asegúrate de que el archivo `supabase.py` ha sido eliminado
2. Verifica que estás usando `supabase_client.py` en su lugar
3. Comprueba que `db_operations.py` importa desde `supabase_client`

### Error de Variables de Entorno

Si encuentras errores relacionados con variables de entorno faltantes:

1. Verifica que todas las variables de entorno están configuradas en Render
2. Comprueba que los nombres de las variables coinciden exactamente con los esperados en el código
3. Asegúrate de que no hay espacios o caracteres especiales en los valores

### Error de Timeout

Si encuentras errores de timeout durante la inicialización:

1. Asegúrate de que estás usando el parámetro `--timeout 120` en el comando de inicio
2. Si el problema persiste, considera aumentar el timeout a 180 o 240 segundos

## Rollback

Si necesitas volver a la aplicación simplificada:

1. Ve a la sección "Settings" de tu servicio en Render
2. Cambia el comando de inicio de vuelta a:
   ```
   gunicorn simple_app:app --timeout 120
   ```
3. Haz clic en "Save Changes"
4. Realiza un nuevo despliegue manual

## Recursos Adicionales

- [Documentación de Render](https://render.com/docs)
- [Documentación de WhatsApp Business API](https://developers.facebook.com/docs/whatsapp)
- [Documentación de Flask](https://flask.palletsprojects.com/)
- [Documentación de Gunicorn](https://docs.gunicorn.org/)
