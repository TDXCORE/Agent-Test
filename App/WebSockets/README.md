# Módulo WebSockets

Este módulo proporciona una implementación de WebSockets para reemplazar las APIs REST existentes, permitiendo comunicación en tiempo real entre el servidor y los clientes.

## Características

- **Comunicación bidireccional en tiempo real**: Permite actualizaciones instantáneas sin necesidad de polling.
- **Gestión de conexiones**: Manejo eficiente de conexiones WebSocket con agrupación por usuario y conversación.
- **Sistema de eventos**: Arquitectura basada en eventos para notificaciones en tiempo real.
- **Autenticación**: Soporte para autenticación mediante tokens JWT.
- **Operaciones CRUD**: Soporte completo para operaciones de consulta, creación, actualización y eliminación.
- **Integración con APIs existentes**: Middleware para notificar eventos desde las APIs REST existentes.
- **Reconexión automática**: El cliente maneja reconexiones automáticas con backoff exponencial.
- **Heartbeats**: Detección de conexiones inactivas y limpieza automática.

## Estructura del módulo

```
App/WebSockets/
├── __init__.py           # Exportación de componentes principales
├── main.py               # Punto de entrada y configuración principal
├── connection.py         # Gestor de conexiones WebSocket
├── auth.py               # Autenticación para WebSockets
├── setup.py              # Configuración de WebSockets en la aplicación
├── integration.py        # Integración con la aplicación principal
├── client.py             # Cliente WebSocket para Python
├── frontend_integration.js # Integración con el frontend
├── events/               # Sistema de eventos
│   ├── __init__.py
│   ├── dispatcher.py     # Dispatcher de eventos
│   └── listeners.py      # Listeners de eventos
├── handlers/             # Handlers para diferentes recursos
│   ├── __init__.py
│   ├── base.py           # Handler base
│   ├── conversations.py  # Handler para conversaciones
│   ├── messages.py       # Handler para mensajes
│   └── users.py          # Handler para usuarios
└── models/               # Modelos de datos
    ├── __init__.py
    └── base.py           # Modelos base
```

## Instalación

1. Asegúrate de tener las dependencias necesarias:

```bash
pip install fastapi websockets pydantic
```

2. Integra el módulo WebSockets en tu aplicación FastAPI:

```python
# En App/api.py
from fastapi import FastAPI
from App.WebSockets.integration import integrate_websockets

app = FastAPI()

# Configurar rutas y dependencias...

# Integrar WebSockets
integrate_websockets()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Pruebas rápidas

Para probar rápidamente la implementación de WebSockets sin modificar la aplicación principal:

### Opción 1: Prueba automatizada (recomendado)

Ejecuta el script de prueba automatizada que inicia tanto el servidor como el cliente:

```bash
python -m App.WebSockets.run_test
```

Este script inicia el servidor, espera a que esté listo, ejecuta el cliente y muestra la salida de ambos procesos en tiempo real.

### Opción 2: Prueba manual

1. Inicia el servidor de prueba:

```bash
python -m App.WebSockets.test_server
```

2. En otra terminal, ejecuta el cliente de prueba:

```bash
python -m App.WebSockets.simple_test
```

También puedes verificar que el servidor está funcionando correctamente abriendo http://localhost:8000 en tu navegador.

## Uso en el backend

### Inicialización

```python
from App.WebSockets.main import init_websockets
from fastapi import FastAPI

app = FastAPI()
init_websockets(app)
```

### Notificar eventos

```python
from App.WebSockets.main import notify_event

# Notificar un nuevo mensaje
await notify_event("new_message", {
    "conversation_id": "conv123",
    "message": {
        "id": "msg456",
        "content": "Hola mundo",
        "sender_id": "user789",
        "timestamp": "2025-05-20T12:34:56Z"
    }
})
```

## Uso en el frontend

### Inicialización

```javascript
// Importar cliente WebSocket
import { createWebSocketClient } from '../services/websocketService';

// Crear cliente
const client = createWebSocketClient('mi-token-jwt');

// Conectar
client.connect();

// Registrar callbacks
client.onConnect = (data) => {
    console.log('Conectado:', data);
};

client.onDisconnect = (data) => {
    console.log('Desconectado:', data);
};

client.onError = (error) => {
    console.error('Error:', error);
};
```

### Solicitar datos

```javascript
// Obtener todas las conversaciones
client.send('conversations', 'get_all', { user_id: 'user123' }, (data, error) => {
    if (error) {
        console.error('Error al obtener conversaciones:', error);
        return;
    }
    
    console.log('Conversaciones:', data.conversations);
});

// Crear un nuevo mensaje
client.send('messages', 'create', {
    message: {
        conversation_id: 'conv123',
        content: 'Hola mundo',
        sender_id: 'user789'
    }
}, (data, error) => {
    if (error) {
        console.error('Error al crear mensaje:', error);
        return;
    }
    
    console.log('Mensaje creado:', data.message);
});
```

### Suscribirse a eventos

```javascript
// Suscribirse a nuevos mensajes
client.on('new_message', (message) => {
    console.log('Nuevo mensaje recibido:', message);
    // Actualizar UI
});

// Suscribirse a eliminación de mensajes
client.on('message_deleted', (data) => {
    console.log('Mensaje eliminado:', data.message_id);
    // Actualizar UI
});
```

## Protocolo de mensajes

### Mensajes del cliente al servidor

#### Solicitud de recurso

```json
{
  "type": "request",
  "id": "msg-123456789",
  "resource": "conversations",
  "payload": {
    "action": "get_all",
    "user_id": "user123"
  }
}
```

### Mensajes del servidor al cliente

#### Respuesta a solicitud

```json
{
  "type": "response",
  "id": "msg-123456789",
  "payload": {
    "conversations": [
      {
        "id": "conv123",
        "title": "Conversación 1",
        "created_at": "2025-05-20T12:34:56Z"
      },
      {
        "id": "conv456",
        "title": "Conversación 2",
        "created_at": "2025-05-20T12:45:00Z"
      }
    ]
  }
}
```

#### Evento

```json
{
  "type": "event",
  "id": "evt-987654321",
  "payload": {
    "type": "new_message",
    "data": {
      "id": "msg456",
      "conversation_id": "conv123",
      "content": "Hola mundo",
      "sender_id": "user789",
      "timestamp": "2025-05-20T12:34:56Z"
    }
  }
}
```

#### Error

```json
{
  "type": "error",
  "id": "msg-123456789",
  "payload": {
    "code": "not_found",
    "message": "Conversación no encontrada",
    "details": {
      "conversation_id": "conv999"
    }
  }
}
```

## Consideraciones de seguridad

- **Autenticación**: Todos los WebSockets deben autenticarse mediante token JWT.
- **Validación**: Todos los mensajes son validados usando Pydantic.
- **Rate limiting**: Implementar rate limiting para prevenir abuso.
- **Timeout**: Las conexiones inactivas son cerradas automáticamente después de 5 minutos.

## Rendimiento y escalabilidad

- **Conexiones concurrentes**: El sistema está diseñado para manejar miles de conexiones concurrentes.
- **Memoria**: Cada conexión consume aproximadamente 10KB de memoria.
- **CPU**: El procesamiento de mensajes es asíncrono y eficiente.
- **Escalabilidad horizontal**: Para escalar más allá de un solo servidor, se recomienda usar Redis para compartir estado entre instancias.

## Integración con el frontend existente

Ver el archivo `frontend_integration.js` para ejemplos de cómo integrar el cliente WebSocket en una aplicación React/Next.js.

## Migración desde APIs REST

Este módulo está diseñado para reemplazar gradualmente las APIs REST existentes. Durante la transición, ambos sistemas pueden coexistir, con el middleware de integración asegurando que los eventos se propaguen correctamente.

## Contribución

1. Sigue las convenciones de código existentes.
2. Añade pruebas para nuevas funcionalidades.
3. Documenta cualquier cambio en la API.
