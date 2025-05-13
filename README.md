# Backend Repository

Este repositorio contiene el código del backend para el sistema de chat y calificación de leads.

## Estructura del Repositorio

```
App/
├── __init__.py
├── api.py                 # Punto de entrada principal
├── dependencies.py        # Dependencias comunes
├── Agent/                 # Módulo del agente de IA
│   ├── __init__.py
│   └── main.py            # Implementación del agente
├── Api/                   # Endpoints de API para el frontend
│   ├── __init__.py
│   ├── conversations.py   # Gestión de conversaciones
│   ├── messages.py        # Gestión de mensajes
│   └── users.py           # Gestión de usuarios
├── DB/                    # Capa de acceso a datos
│   ├── __init__.py
│   ├── db_operations.py   # Operaciones de base de datos
│   └── supabase_client.py # Cliente de Supabase
├── Schema/                # Esquemas de base de datos
│   ├── __init__.py
│   └── supabase_schema.sql # Definición de tablas
└── Services/              # Servicios externos
    ├── __init__.py
    ├── outlook.py         # Integración con Outlook/Microsoft Graph
    ├── simple_webhook.py  # Webhook para WhatsApp
    └── whatsapp_api.py    # Cliente de WhatsApp API
Test/                      # Scripts de prueba
├── __init__.py
```

## Flujos Principales

### 1. Flujo de Mensajes de WhatsApp (Meta API)

1. Los mensajes entrantes de WhatsApp llegan a `/webhook` en `App/api.py`
2. Se enrutan a `App/Services/simple_webhook.py`
3. El webhook procesa el mensaje y lo envía al agente en `App/Agent/main.py`
4. El agente puede usar Outlook (`App/Services/outlook.py`) para agendar reuniones
5. La respuesta se envía de vuelta al usuario a través de `App/Services/whatsapp_api.py`
6. Todas las conversaciones y datos se guardan en Supabase mediante `App/DB/db_operations.py`

### 2. Flujo de API para Frontend

1. Las solicitudes del frontend llegan a `App/api.py`
2. Se enrutan a los endpoints correspondientes:
   - `App/Api/conversations.py` para gestionar conversaciones
   - `App/Api/messages.py` para gestionar mensajes
   - `App/Api/users.py` para gestionar usuarios
3. Los endpoints interactúan con la base de datos mediante `App/DB/db_operations.py`

## Configuración del Entorno

1. Crea un archivo `.env` basado en `.env.example` con tus credenciales
2. Instala las dependencias: `pip install -r requirements.txt`

## Ejecución Local

Para ejecutar la aplicación localmente:

```bash
uvicorn App.api:app --reload
```

## Despliegue en Render

Este repositorio está configurado para ser desplegado en Render. Los archivos de configuración son:

- `Procfile`: Configuración para el servicio web
- `render.yaml`: Configuración para los servicios en Render

Para desplegar en Render:

1. Conecta tu repositorio a Render
2. Configura las variables de entorno en el panel de Render
3. Render usará automáticamente la configuración en `render.yaml`
