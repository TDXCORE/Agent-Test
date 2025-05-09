# Integración de WhatsApp con Agente de IA

Este documento explica cómo configurar, desplegar y probar la integración de WhatsApp con el agente de IA.

## Configuración Inicial

### 1. Variables de Entorno

Asegúrate de que las siguientes variables de entorno estén configuradas en tu archivo `.env` y en el panel de Render:

```
# WhatsApp API
WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id
WHATSAPP_ACCESS_TOKEN=tu_access_token
WHATSAPP_WEBHOOK_TOKEN=tu_webhook_token
WHATSAPP_APP_SECRET=tu_app_secret

# OpenAI y LangSmith
OPENAI_API_KEY=tu_openai_api_key
LANGCHAIN_API_KEY=tu_langchain_api_key
LANGSMITH_PROJECT=tu_langsmith_project

# Supabase
NEXT_PUBLIC_SUPABASE_URL=tu_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=tu_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=tu_supabase_service_role_key

# URL de la aplicación desplegada (para check_status.py)
APP_URL=https://tu-app.onrender.com
```

### 2. Archivos de Configuración

Verifica que los siguientes archivos estén correctamente configurados:

- `Procfile`: Debe contener `web: gunicorn simple_webhook:app --timeout 120`
- `render.yaml`: Debe usar `simple_webhook:app` como comando de inicio

## Despliegue

### 1. Desplegar en Render

1. Asegúrate de que todos los cambios estén confirmados en tu repositorio
2. Conéctate a Render y configura un nuevo servicio web
3. Selecciona tu repositorio y configura las variables de entorno
4. Despliega la aplicación

### 2. Configurar Webhook en Meta for Developers

1. Ve a [Meta for Developers](https://developers.facebook.com/)
2. Selecciona tu aplicación
3. Ve a WhatsApp > Configuración
4. En la sección "Webhooks", configura:
   - URL de Callback: `https://tu-app.onrender.com/webhook`
   - Token de Verificación: El mismo valor que usaste en `WHATSAPP_WEBHOOK_TOKEN`
   - Suscríbete a los campos `messages` y `message_status`

## Pruebas

### 1. Verificar Configuración

Usa el script `check_status.py` para verificar la configuración:

```bash
python check_status.py
```

Este script te permitirá:
- Verificar el estado del webhook
- Comprobar la conexión con la API de WhatsApp
- Verificar la salud general de la aplicación
- Enviar un mensaje de prueba

### 2. Enviar Mensajes de Prueba

Usa el script `test_whatsapp_send.py` para enviar mensajes de prueba:

```bash
python test_whatsapp_send.py
```

### 3. Flujo Completo de Prueba

1. Envía un mensaje al número de WhatsApp configurado
2. Verifica en los logs de Render que el webhook reciba el mensaje
3. Comprueba que el agente procese el mensaje (logs en Render y LangSmith)
4. Verifica que recibas una respuesta en WhatsApp

## Solución de Problemas

### Logs y Monitoreo

- **Logs de Render**: Revisa los logs en el panel de Render para ver los mensajes de debug
- **LangSmith**: Verifica las ejecuciones del agente en LangSmith
- **Supabase**: Comprueba que los mensajes se estén guardando en la base de datos

### Problemas Comunes

1. **No se reciben mensajes en el webhook**:
   - Verifica la configuración del webhook en Meta for Developers
   - Comprueba que la URL sea accesible públicamente
   - Revisa los logs para ver si hay errores de autenticación

2. **El webhook recibe mensajes pero no hay respuesta**:
   - Verifica que `simple_webhook.py` esté siendo usado (no `simple_app.py`)
   - Comprueba los logs para ver si hay errores en el procesamiento
   - Verifica que el agente se esté invocando correctamente

3. **Errores de autenticación**:
   - Asegúrate de que todas las variables de entorno estén correctamente configuradas
   - Verifica que los tokens de acceso no hayan expirado

## Estructura del Proyecto

- `simple_webhook.py`: Implementación principal del webhook
- `main.py`: Implementación del agente de IA
- `db_operations.py`: Operaciones de base de datos
- `test_whatsapp_send.py`: Script para enviar mensajes de prueba
- `check_status.py`: Herramienta de diagnóstico

## Notas Adicionales

- El sistema está configurado para usar logging detallado, lo que facilita el diagnóstico de problemas
- Todos los mensajes y respuestas se guardan en la base de datos para referencia futura
- El agente está configurado para usar LangSmith para monitoreo y mejora continua
