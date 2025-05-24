# Documentación de Nuevos Handlers WebSocket

Este documento describe los 4 nuevos handlers especializados para el sistema de WebSockets, diseñados para trabajar con la estructura real de la base de datos.

## 📊 DashboardHandler

Proporciona métricas y estadísticas en tiempo real para el dashboard administrativo.

### Acciones Disponibles

#### `get_dashboard_stats`
Obtiene estadísticas generales del dashboard.

```javascript
{
  "resource": "dashboard",
  "action": "get_dashboard_stats",
  "id": "unique-message-id"
}
```

**Respuesta:**
```javascript
{
  "type": "success",
  "id": "unique-message-id",
  "payload": {
    "data": {
      "total_users": 150,
      "active_conversations": 25,
      "meetings_today": 8,
      "leads_by_step": {
        "start": 45,
        "consent": 30,
        "personal_data": 20,
        "bant": 15,
        "requirements": 10,
        "meeting": 5,
        "completed": 3
      }
    }
  }
}
```

#### `get_conversion_funnel`
Obtiene datos del embudo de conversión por etapas.

```javascript
{
  "resource": "dashboard",
  "action": "get_conversion_funnel",
  "id": "unique-message-id"
}
```

#### `get_activity_timeline`
Obtiene actividad de las últimas 24 horas.

```javascript
{
  "resource": "dashboard",
  "action": "get_activity_timeline",
  "id": "unique-message-id"
}
```

#### `get_agent_performance`
Obtiene métricas de rendimiento del agente IA.

```javascript
{
  "resource": "dashboard",
  "action": "get_agent_performance",
  "id": "unique-message-id"
}
```

#### `get_real_time_metrics`
Obtiene métricas en tiempo real del sistema.

```javascript
{
  "resource": "dashboard",
  "action": "get_real_time_metrics",
  "id": "unique-message-id"
}
```

---

## 👥 LeadsHandler

Gestiona leads y su proceso de calificación completo.

### Acciones Disponibles

#### `get_all_leads`
Obtiene todos los leads con datos completos (JOIN con bant_data y requirements).

```javascript
{
  "resource": "leads",
  "action": "get_all_leads",
  "id": "unique-message-id"
}
```

**Respuesta:**
```javascript
{
  "type": "success",
  "id": "unique-message-id",
  "payload": {
    "data": [
      {
        "id": "lead-id",
        "user_id": "user-id",
        "conversation_id": "conv-id",
        "current_step": "bant",
        "consent": true,
        "user": {
          "full_name": "Juan Pérez",
          "email": "juan@empresa.com",
          "phone": "+1234567890",
          "company": "Empresa ABC"
        },
        "bant_data": {
          "budget": "10000-50000",
          "authority": "decision_maker",
          "need": "urgent",
          "timeline": "3_months"
        },
        "requirements": {
          "app_type": "web_app",
          "deadline": "2024-06-01"
        }
      }
    ]
  }
}
```

#### `get_lead_pipeline`
Obtiene el pipeline de leads agrupado por etapa.

```javascript
{
  "resource": "leads",
  "action": "get_lead_pipeline",
  "id": "unique-message-id"
}
```

#### `get_lead_with_complete_data`
Obtiene un lead específico con todo su ecosistema de datos.

```javascript
{
  "resource": "leads",
  "action": "get_lead_with_complete_data",
  "payload": {
    "lead_id": "lead-qualification-id"
  },
  "id": "unique-message-id"
}
```

#### `update_lead_step`
Actualiza manualmente el paso actual de un lead.

```javascript
{
  "resource": "leads",
  "action": "update_lead_step",
  "payload": {
    "lead_id": "lead-qualification-id",
    "new_step": "requirements"
  },
  "id": "unique-message-id"
}
```

#### `get_conversion_stats`
Obtiene estadísticas de conversión entre etapas.

```javascript
{
  "resource": "leads",
  "action": "get_conversion_stats",
  "id": "unique-message-id"
}
```

#### `get_abandoned_leads`
Obtiene leads abandonados (sin completar por más de 7 días).

```javascript
{
  "resource": "leads",
  "action": "get_abandoned_leads",
  "id": "unique-message-id"
}
```

---

## 📅 MeetingsHandler

Gestiona reuniones y sincronización con Outlook.

### Acciones Disponibles

#### `get_all_meetings`
Obtiene todas las reuniones con filtros opcionales.

```javascript
{
  "resource": "meetings",
  "action": "get_all_meetings",
  "payload": {
    "filter": "today" // "today", "this_week", "by_status"
  },
  "id": "unique-message-id"
}
```

#### `get_calendar_view`
Obtiene vista de calendario agrupada por fecha.

```javascript
{
  "resource": "meetings",
  "action": "get_calendar_view",
  "payload": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "id": "unique-message-id"
}
```

#### `create_meeting`
Crea una nueva reunión y la sincroniza con Outlook.

```javascript
{
  "resource": "meetings",
  "action": "create_meeting",
  "payload": {
    "user_id": "user-id",
    "lead_qualification_id": "lead-id",
    "subject": "Reunión de seguimiento",
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T11:00:00Z",
    "attendee_email": "cliente@empresa.com"
  },
  "id": "unique-message-id"
}
```

#### `update_meeting`
Actualiza una reunión existente.

```javascript
{
  "resource": "meetings",
  "action": "update_meeting",
  "payload": {
    "meeting_id": "meeting-id",
    "subject": "Nuevo asunto",
    "start_time": "2024-01-15T14:00:00Z",
    "end_time": "2024-01-15T15:00:00Z"
  },
  "id": "unique-message-id"
}
```

#### `cancel_meeting`
Cancela una reunión.

```javascript
{
  "resource": "meetings",
  "action": "cancel_meeting",
  "payload": {
    "meeting_id": "meeting-id"
  },
  "id": "unique-message-id"
}
```

#### `get_available_slots`
Obtiene slots disponibles para agendar reuniones.

```javascript
{
  "resource": "meetings",
  "action": "get_available_slots",
  "payload": {
    "date": "2024-01-15",
    "duration": 60 // minutos
  },
  "id": "unique-message-id"
}
```

#### `sync_outlook_calendar`
Sincroniza el calendario con Outlook.

```javascript
{
  "resource": "meetings",
  "action": "sync_outlook_calendar",
  "id": "unique-message-id"
}
```

---

## 📋 RequirementsHandler

Gestiona requerimientos, features e integraciones.

### Acciones Disponibles

#### `get_requirements_by_lead`
Obtiene requerimientos completos de un lead (con features e integraciones).

```javascript
{
  "resource": "requirements",
  "action": "get_requirements_by_lead",
  "payload": {
    "lead_id": "lead-qualification-id"
  },
  "id": "unique-message-id"
}
```

**Respuesta:**
```javascript
{
  "type": "success",
  "id": "unique-message-id",
  "payload": {
    "data": {
      "id": "requirement-id",
      "app_type": "web_app",
      "deadline": "2024-06-01",
      "features": [
        {
          "id": "feature-id",
          "name": "Sistema de autenticación",
          "description": "Login con email y contraseña"
        }
      ],
      "integrations": [
        {
          "id": "integration-id",
          "name": "PayPal",
          "description": "Procesamiento de pagos"
        }
      ]
    }
  }
}
```

#### `create_requirement_package`
Crea un paquete completo de requerimientos en una transacción.

```javascript
{
  "resource": "requirements",
  "action": "create_requirement_package",
  "payload": {
    "lead_qualification_id": "lead-id",
    "app_type": "mobile_app",
    "deadline": "2024-08-01",
    "features": [
      {
        "name": "Push Notifications",
        "description": "Notificaciones en tiempo real"
      }
    ],
    "integrations": [
      {
        "name": "Firebase",
        "description": "Backend como servicio"
      }
    ]
  },
  "id": "unique-message-id"
}
```

#### `update_requirements`
Actualiza requerimientos básicos.

```javascript
{
  "resource": "requirements",
  "action": "update_requirements",
  "payload": {
    "requirements_id": "requirement-id",
    "app_type": "web_app",
    "deadline": "2024-07-01"
  },
  "id": "unique-message-id"
}
```

#### `add_feature`
Añade una feature a los requerimientos.

```javascript
{
  "resource": "requirements",
  "action": "add_feature",
  "payload": {
    "requirements_id": "requirement-id",
    "name": "Chat en vivo",
    "description": "Sistema de chat en tiempo real"
  },
  "id": "unique-message-id"
}
```

#### `add_integration`
Añade una integración a los requerimientos.

```javascript
{
  "resource": "requirements",
  "action": "add_integration",
  "payload": {
    "requirements_id": "requirement-id",
    "name": "Stripe",
    "description": "Procesamiento de pagos"
  },
  "id": "unique-message-id"
}
```

#### `get_popular_features`
Obtiene las features más populares.

```javascript
{
  "resource": "requirements",
  "action": "get_popular_features",
  "id": "unique-message-id"
}
```

#### `get_popular_integrations`
Obtiene las integraciones más populares.

```javascript
{
  "resource": "requirements",
  "action": "get_popular_integrations",
  "id": "unique-message-id"
}
```

---

## 🔧 Campo Crítico: agent_enabled

Todos los handlers respetan el campo `conversations.agent_enabled` para activar/desactivar el agente IA:

```javascript
// Para activar/desactivar el agente en una conversación
{
  "resource": "conversations",
  "action": "update_agent_status",
  "payload": {
    "conversation_id": "conv-id",
    "enabled": true // o false
  },
  "id": "unique-message-id"
}
```

---

## 🧪 Pruebas

Para probar todos los handlers, ejecuta:

```bash
python App/WebSockets/test_new_handlers.py
```

Este script prueba todas las funcionalidades de los 4 nuevos handlers.

---

## 📁 Estructura de Archivos

```
App/WebSockets/handlers/
├── dashboard.py          # Handler para métricas del dashboard
├── leads.py             # Handler para gestión de leads
├── meetings.py          # Handler para reuniones y Outlook
├── requirements.py      # Handler para requerimientos
└── ...
```

---

## 🔄 Integración con Frontend

Ejemplo de uso desde JavaScript:

```javascript
// Conectar al WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// Obtener estadísticas del dashboard
ws.send(JSON.stringify({
  resource: 'dashboard',
  action: 'get_dashboard_stats',
  id: generateUniqueId()
}));

// Escuchar respuestas
ws.onmessage = (event) => {
  const response = JSON.parse(event.data);
  console.log('Respuesta:', response);
};
```

---

## ⚡ Características Especiales

1. **Transacciones**: Los handlers manejan transacciones para operaciones complejas
2. **JOINs Optimizados**: Consultas eficientes con múltiples tablas
3. **Tiempo Real**: Métricas actualizadas en tiempo real
4. **Sincronización**: Integración completa con Outlook
5. **Validación**: Validación robusta de datos de entrada
6. **Logging**: Logging detallado para debugging
7. **Error Handling**: Manejo de errores comprehensivo

---

## 🚀 Próximos Pasos

1. Ejecutar las pruebas para verificar funcionamiento
2. Integrar con el frontend
3. Configurar notificaciones en tiempo real
4. Implementar caching para mejor rendimiento
5. Añadir más métricas según necesidades del negocio
