# Guía de Integración de WebSockets

Esta guía explica cómo integrar el módulo WebSockets en la aplicación existente.

## 1. Modificar api.py

El primer paso es modificar el archivo `App/api.py` para integrar los WebSockets. Aquí hay un ejemplo de cómo hacerlo:

```python
# Importaciones existentes
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="FullStackAgent API",
    description="API para la aplicación FullStackAgent",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar rutas API existentes
from App.Api.conversations import router as conversations_router
from App.Api.messages import router as messages_router
from App.Api.users import router as users_router

# Registrar rutas
app.include_router(conversations_router, prefix="/api/conversations", tags=["conversations"])
app.include_router(messages_router, prefix="/api/messages", tags=["messages"])
app.include_router(users_router, prefix="/api/users", tags=["users"])

# NUEVO: Importar e integrar WebSockets
from App.WebSockets.integration import integrate_websockets

# NUEVO: Integrar WebSockets con la aplicación
integrate_websockets()

# Punto de entrada para ejecución directa
if __name__ == "__main__":
    import uvicorn
    
    # Obtener puerto de variables de entorno o usar 8000 por defecto
    port = int(os.getenv("PORT", 8000))
    
    # Iniciar servidor
    uvicorn.run(
        "App.api:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
```

## 2. Actualizar requirements.txt

Asegúrate de que las dependencias necesarias estén en el archivo `requirements.txt`:

```
fastapi>=0.68.0
uvicorn>=0.15.0
websockets>=10.0
pydantic>=1.8.0
```

## 3. Iniciar el servidor

Una vez realizados los cambios, puedes iniciar el servidor:

```bash
python -m App.api
```

## 4. Probar la integración

### 4.1 Prueba automatizada (recomendado)

La forma más sencilla de probar la integración es usar el script `run_test.py`, que inicia automáticamente tanto el servidor como el cliente:

```bash
python -m App.WebSockets.run_test
```

Este script:
1. Inicia el servidor de prueba
2. Espera a que el servidor esté listo (5 segundos)
3. Ejecuta el cliente de prueba
4. Muestra la salida de ambos procesos en tiempo real
5. Termina el servidor cuando el cliente ha finalizado

### 4.2 Prueba manual (alternativa)

Si prefieres ejecutar el servidor y cliente manualmente:

#### 4.2.1 Iniciar el servidor de prueba

En una terminal, inicia el servidor de prueba:

```bash
python -m App.WebSockets.test_server
```

Esto iniciará un servidor FastAPI con WebSockets habilitados en http://localhost:8000, con el endpoint WebSocket disponible en ws://localhost:8000/ws.

#### 4.2.2 Ejecutar el cliente de prueba

En otra terminal, ejecuta el cliente de prueba:

```bash
python -m App.WebSockets.simple_test
```

Si todo funciona correctamente, deberías ver mensajes de conexión exitosa y respuestas del servidor.

### 4.3 Verificar en el navegador

También puedes verificar que el servidor está funcionando correctamente abriendo http://localhost:8000 en tu navegador. Deberías ver un mensaje JSON indicando que el servidor está funcionando.

## 5. Integración en el frontend

Para integrar los WebSockets en el frontend, puedes usar el archivo `frontend_integration.js` como referencia. Aquí hay un ejemplo básico:

```javascript
// src/services/websocketService.js
export const createWebSocketClient = (token) => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const wsProtocol = baseUrl.startsWith('https') ? 'wss' : 'ws';
  const wsUrl = `${wsProtocol}://${baseUrl.replace(/^https?:\/\//, '')}/ws`;
  
  return new WebSocketClient(wsUrl, token);
};

// En un componente React
import { useEffect } from 'react';
import { createWebSocketClient } from '../services/websocketService';

function MyComponent() {
  useEffect(() => {
    const client = createWebSocketClient('mi-token-jwt');
    
    client.onConnect = (data) => {
      console.log('Conectado:', data);
    };
    
    client.connect();
    
    // Limpiar al desmontar
    return () => {
      client.disconnect();
    };
  }, []);
  
  return <div>Mi componente</div>;
}
```

## 6. Migración gradual

Puedes migrar gradualmente de las APIs REST a WebSockets:

1. Primero, integra los WebSockets manteniendo las APIs REST existentes.
2. Actualiza el frontend para usar WebSockets para operaciones en tiempo real.
3. Gradualmente, migra más funcionalidades a WebSockets.
4. Eventualmente, puedes deprecar las APIs REST si ya no son necesarias.

## 7. Consideraciones de producción

Para entornos de producción, considera:

- Configurar un proxy como Nginx para manejar las conexiones WebSocket.
- Implementar rate limiting para prevenir abuso.
- Configurar timeouts adecuados.
- Monitorear el número de conexiones activas.
- Usar Redis para compartir estado entre múltiples instancias si necesitas escalar horizontalmente.

## 8. Solución de problemas

Si encuentras problemas:

- Verifica los logs del servidor para errores.
- Usa las herramientas de desarrollo del navegador para inspeccionar las conexiones WebSocket.
- Asegúrate de que no haya firewalls o proxies bloqueando las conexiones WebSocket.
- Verifica que estás usando el protocolo correcto (ws:// o wss://).
