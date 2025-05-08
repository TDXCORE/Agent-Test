# Configuración de Supabase para el Sistema de Calificación de Leads

Este documento proporciona instrucciones para configurar y utilizar la base de datos Supabase en el sistema de calificación de leads.

## Índice

1. [Introducción](#introducción)
2. [Requisitos Previos](#requisitos-previos)
3. [Configuración de Supabase](#configuración-de-supabase)
4. [Estructura de la Base de Datos](#estructura-de-la-base-de-datos)
5. [Integración con el Sistema](#integración-con-el-sistema)
6. [Operaciones Comunes](#operaciones-comunes)
7. [Solución de Problemas](#solución-de-problemas)

## Introducción

Supabase es una alternativa de código abierto a Firebase que proporciona una base de datos PostgreSQL con una API RESTful. En este proyecto, utilizamos Supabase para almacenar y gestionar los datos de los usuarios, conversaciones, mensajes y calificaciones de leads.

## Requisitos Previos

- Cuenta en [Supabase](https://supabase.com/)
- Python 3.8 o superior
- Paquetes de Python: `supabase`, `python-dotenv`

## Configuración de Supabase

### 1. Crear un Proyecto en Supabase

1. Inicia sesión en [Supabase](https://supabase.com/)
2. Haz clic en "New Project"
3. Completa la información del proyecto:
   - Nombre del proyecto
   - Contraseña de la base de datos
   - Región (preferiblemente cerca de tus usuarios)
4. Haz clic en "Create new project"

### 2. Obtener Credenciales

Una vez creado el proyecto, necesitarás las siguientes credenciales:

1. URL de Supabase: En la sección "Settings" > "API" > "Project URL"
2. Clave Anónima: En la sección "Settings" > "API" > "anon public"
3. Clave de Servicio: En la sección "Settings" > "API" > "service_role secret"

### 3. Configurar Variables de Entorno

Añade las siguientes variables a tu archivo `.env`:

```
NEXT_PUBLIC_SUPABASE_URL=https://tu-proyecto.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=tu-clave-anon
SUPABASE_SERVICE_ROLE_KEY=tu-clave-service-role
```

### 4. Crear la Estructura de la Base de Datos

Ejecuta el script SQL proporcionado en `supabase_schema.sql` en el Editor SQL de Supabase:

1. Ve a la sección "SQL Editor" en el panel de control de Supabase
2. Crea un nuevo script
3. Copia y pega el contenido de `supabase_schema.sql`
4. Ejecuta el script

## Estructura de la Base de Datos

La base de datos consta de las siguientes tablas:

1. **users**: Almacena información de los usuarios
   - `id`: UUID, clave primaria
   - `phone`: Número de teléfono (único)
   - `email`: Correo electrónico (único)
   - `full_name`: Nombre completo
   - `company`: Empresa
   - `created_at`: Fecha de creación
   - `updated_at`: Fecha de actualización

2. **conversations**: Almacena las conversaciones
   - `id`: UUID, clave primaria
   - `user_id`: ID del usuario (clave foránea)
   - `platform`: Plataforma (whatsapp, web, etc.)
   - `external_id`: ID externo (número de teléfono para WhatsApp)
   - `status`: Estado (active, closed)
   - `created_at`: Fecha de creación
   - `updated_at`: Fecha de actualización

3. **messages**: Almacena los mensajes de las conversaciones
   - `id`: UUID, clave primaria
   - `conversation_id`: ID de la conversación (clave foránea)
   - `role`: Rol del mensaje (user, assistant, system)
   - `content`: Contenido del mensaje
   - `message_type`: Tipo de mensaje (text, image, audio, video)
   - `media_url`: URL del archivo multimedia
   - `external_id`: ID externo del mensaje
   - `created_at`: Fecha de creación

4. **lead_qualification**: Almacena la calificación de leads
   - `id`: UUID, clave primaria
   - `user_id`: ID del usuario (clave foránea)
   - `conversation_id`: ID de la conversación (clave foránea)
   - `consent`: Consentimiento GDPR/LPD
   - `current_step`: Paso actual del proceso
   - `created_at`: Fecha de creación
   - `updated_at`: Fecha de actualización

5. **bant_data**: Almacena los datos BANT
   - `id`: UUID, clave primaria
   - `lead_qualification_id`: ID de la calificación de lead (clave foránea)
   - `budget`: Presupuesto
   - `authority`: Nivel de autoridad
   - `need`: Necesidad
   - `timeline`: Plazo
   - `created_at`: Fecha de creación
   - `updated_at`: Fecha de actualización

6. **requirements**: Almacena los requerimientos del proyecto
   - `id`: UUID, clave primaria
   - `lead_qualification_id`: ID de la calificación de lead (clave foránea)
   - `app_type`: Tipo de aplicación
   - `deadline`: Fecha límite
   - `created_at`: Fecha de creación
   - `updated_at`: Fecha de actualización

7. **features**: Almacena las características del proyecto
   - `id`: UUID, clave primaria
   - `requirement_id`: ID de los requerimientos (clave foránea)
   - `name`: Nombre de la característica
   - `description`: Descripción
   - `created_at`: Fecha de creación

8. **integrations**: Almacena las integraciones del proyecto
   - `id`: UUID, clave primaria
   - `requirement_id`: ID de los requerimientos (clave foránea)
   - `name`: Nombre de la integración
   - `description`: Descripción
   - `created_at`: Fecha de creación

9. **meetings**: Almacena las reuniones
   - `id`: UUID, clave primaria
   - `user_id`: ID del usuario (clave foránea)
   - `lead_qualification_id`: ID de la calificación de lead (clave foránea)
   - `outlook_meeting_id`: ID de la reunión en Outlook
   - `subject`: Asunto
   - `start_time`: Fecha y hora de inicio
   - `end_time`: Fecha y hora de fin
   - `status`: Estado (scheduled, completed, cancelled, rescheduled)
   - `online_meeting_url`: URL de la reunión online
   - `created_at`: Fecha de creación
   - `updated_at`: Fecha de actualización

## Integración con el Sistema

El sistema utiliza el archivo `db_operations.py` como capa de abstracción para interactuar con la base de datos. Este archivo proporciona funciones para realizar operaciones CRUD en las diferentes tablas.

### Ejemplo de Uso

```python
from db_operations import get_or_create_user, get_conversation_history

# Obtener o crear un usuario
user = get_or_create_user(
    phone="+1234567890",
    email="usuario@example.com",
    full_name="Nombre Completo",
    company="Empresa"
)

# Obtener historial de conversación
messages = get_conversation_history(conversation_id)
```

## Operaciones Comunes

### Usuarios

- **Obtener usuario por teléfono**: `get_user_by_phone(phone)`
- **Obtener usuario por email**: `get_user_by_email(email)`
- **Crear usuario**: `create_user(user_data)`
- **Actualizar usuario**: `update_user(user_id, user_data)`
- **Obtener o crear usuario**: `get_or_create_user(phone, email, full_name, company)`

### Conversaciones

- **Obtener conversación activa**: `get_active_conversation(external_id, platform)`
- **Crear conversación**: `create_conversation(user_id, external_id, platform)`
- **Cerrar conversación**: `close_conversation(conversation_id)`
- **Obtener o crear conversación**: `get_or_create_conversation(user_id, external_id, platform)`

### Mensajes

- **Obtener mensajes de conversación**: `get_conversation_messages(conversation_id)`
- **Añadir mensaje**: `add_message(conversation_id, role, content, message_type, media_url, external_id)`
- **Obtener historial de conversación**: `get_conversation_history(conversation_id)`

### Calificación de Leads

- **Obtener calificación de lead**: `get_lead_qualification(user_id, conversation_id)`
- **Crear calificación de lead**: `create_lead_qualification(user_id, conversation_id)`
- **Actualizar calificación de lead**: `update_lead_qualification(qualification_id, data)`
- **Obtener o crear calificación de lead**: `get_or_create_lead_qualification(user_id, conversation_id)`

### Datos BANT

- **Obtener datos BANT**: `get_bant_data(lead_qualification_id)`
- **Crear o actualizar datos BANT**: `create_or_update_bant_data(lead_qualification_id, budget, authority, need, timeline)`

### Requerimientos

- **Obtener requerimientos**: `get_requirements(lead_qualification_id)`
- **Crear requerimientos**: `create_requirements(lead_qualification_id, app_type, deadline)`
- **Actualizar requerimientos**: `update_requirements(requirements_id, data)`
- **Obtener o crear requerimientos**: `get_or_create_requirements(lead_qualification_id, app_type, deadline)`

### Características e Integraciones

- **Añadir característica**: `add_feature(requirement_id, name, description)`
- **Obtener características**: `get_features(requirement_id)`
- **Añadir integración**: `add_integration(requirement_id, name, description)`
- **Obtener integraciones**: `get_integrations(requirement_id)`

### Reuniones

- **Crear reunión**: `create_meeting(user_id, lead_qualification_id, outlook_meeting_id, subject, start_time, end_time, online_meeting_url)`
- **Actualizar estado de reunión**: `update_meeting_status(meeting_id, status)`
- **Obtener reuniones de usuario**: `get_user_meetings(user_id)`
- **Obtener reunión por ID de Outlook**: `get_meeting_by_outlook_id(outlook_meeting_id)`

## Solución de Problemas

### Problemas de Conexión

Si tienes problemas para conectarte a Supabase:

1. Verifica que las credenciales en el archivo `.env` sean correctas
2. Asegúrate de que el proyecto de Supabase esté activo
3. Comprueba que la región de Supabase no esté bloqueada por tu red

### Errores en las Consultas

Si encuentras errores al realizar consultas:

1. Verifica que la estructura de la base de datos sea correcta
2. Comprueba que los tipos de datos sean los esperados
3. Revisa los logs de Supabase para ver errores específicos

### Problemas de Permisos

Si tienes problemas de permisos:

1. Asegúrate de estar utilizando la clave de servicio para operaciones que requieren permisos elevados
2. Verifica que las políticas RLS estén configuradas correctamente
3. Comprueba que el usuario tenga los permisos necesarios para realizar la operación
