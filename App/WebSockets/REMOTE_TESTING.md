# Pruebas de WebSocket en Servidor Remoto

Este documento explica cómo probar la implementación de WebSockets en un servidor remoto, específicamente en el servidor desplegado en Render.

## Requisitos

- Python 3.7 o superior
- Paquete `websockets` instalado (`pip install websockets`)
- Acceso al servidor remoto (URL y credenciales si son necesarias)

## Herramientas Disponibles

### 1. remote_websocket_test.py

Este script realiza pruebas exhaustivas de la implementación de WebSockets en un servidor remoto. Prueba:

- Conexión al servidor WebSocket
- Operaciones CRUD para conversaciones
- Operaciones CRUD para mensajes
- Operaciones CRUD para usuarios
- Eventos en tiempo real

### 2. run_remote_test.py

Este script es un wrapper amigable para `remote_websocket_test.py` que facilita su ejecución.

### 3. browser_test.html

Esta interfaz web permite probar la conexión WebSocket directamente desde el navegador, con una interfaz gráfica intuitiva que permite:

- Conectar/desconectar del servidor WebSocket
- Enviar solicitudes para diferentes recursos (conversaciones, mensajes, usuarios)
- Ver las respuestas en tiempo real
- Personalizar parámetros de solicitud
- Visualizar eventos en tiempo real

## Uso Básico

### Pruebas Automatizadas con Python

La forma más sencilla de ejecutar las pruebas automatizadas es usar el script `run_remote_test.py`:

```bash
# Si estás en el directorio raíz del proyecto:
python -m App.WebSockets.run_remote_test

# Si estás dentro del directorio App/WebSockets:
python run_remote_test.py
```

Por defecto, este comando se conectará a `wss://waagentv1.onrender.com/ws` y ejecutará todas las pruebas.

### Pruebas Interactivas con Navegador

Para realizar pruebas interactivas con una interfaz gráfica:

1. Ejecuta el script `serve_browser_test.py` para iniciar un servidor web local y abrir automáticamente el navegador:

```bash
python -m App.WebSockets.serve_browser_test
```

También puedes especificar un puerto diferente:

```bash
python -m App.WebSockets.serve_browser_test --port 9090
```

O simplemente abrir el archivo `browser_test.html` directamente desde el explorador de archivos, aunque esto puede tener limitaciones en algunos navegadores.

2. En la interfaz web:
   - La URL del servidor ya está preconfigurada como `wss://waagentv1.onrender.com/ws`
   - Haz clic en "Conectar" para establecer la conexión WebSocket
   - Una vez conectado, usa las pestañas para enviar diferentes tipos de solicitudes:
     - **Conversaciones**: Operaciones CRUD para conversaciones
     - **Mensajes**: Operaciones CRUD para mensajes
     - **Usuarios**: Operaciones CRUD para usuarios
     - **Personalizado**: Enviar solicitudes personalizadas con cualquier recurso y acción

3. Todas las respuestas y eventos se mostrarán en el panel de "Log de Mensajes"

## Opciones de Configuración

Puedes personalizar las pruebas con varias opciones:

```bash
python -m App.WebSockets.run_remote_test --url otra-url.com --insecure --timeout 15 --debug
```

### Opciones disponibles:

- `--url`: URL base del servidor (sin protocolo). Por defecto: `waagentv1.onrender.com`
- `--token`: Token de autenticación (opcional)
- `--insecure`: Usar conexión no segura (ws:// en lugar de wss://)
- `--timeout`: Timeout en segundos para operaciones. Por defecto: 10
- `--debug`: Activar modo debug para ver más información

## Ejemplos de Uso

### Probar con el servidor por defecto

```bash
python -m App.WebSockets.run_remote_test
```

### Probar con una URL personalizada

```bash
python -m App.WebSockets.run_remote_test --url mi-servidor.com
```

### Probar con conexión no segura (ws:// en lugar de wss://)

```bash
python -m App.WebSockets.run_remote_test --insecure
```

### Probar con un token de autenticación

```bash
python -m App.WebSockets.run_remote_test --token mi-token-jwt
```

### Aumentar el timeout para servidores lentos

```bash
python -m App.WebSockets.run_remote_test --timeout 30
```

### Activar modo debug para ver más información

```bash
python -m App.WebSockets.run_remote_test --debug
```

## Interpretación de Resultados

Al finalizar las pruebas, se mostrará un reporte detallado con:

1. Resumen de pruebas exitosas y fallidas
2. Detalles de cada prueba
3. Datos de respuesta (truncados si son muy largos)
4. Recomendaciones basadas en los resultados

### Ejemplo de reporte:

```
================================================================================
REPORTE DE PRUEBAS WEBSOCKET - waagentv1.onrender.com
================================================================================

Resumen: 8/10 pruebas exitosas (2 fallidas)
--------------------------------------------------------------------------------

1. connection - ✅ ÉXITO
   Mensaje: Conexión exitosa

2. conversations.get_all - ✅ ÉXITO
   Mensaje: Obtenidas conversaciones correctamente
   Datos: {"conversations": [...]}

3. conversations.create - ✅ ÉXITO
   Mensaje: Conversación creada: conv-123
   Datos: {"conversation": {...}}

...

9. real_time_events - ❌ FALLO
   Mensaje: No se recibieron eventos

================================================================================

Recomendaciones:
- Verifica la implementación del sistema de eventos
- Comprueba que los eventos se estén disparando correctamente

================================================================================
```

## Solución de Problemas

### Error de conexión

Si ves errores como "Error al conectar" o "Timeout al conectar", verifica:

1. Que el servidor esté en ejecución
2. Que la URL sea correcta
3. Que estés usando el protocolo correcto (wss:// o ws://)
4. Que no haya firewalls bloqueando la conexión

### Errores en operaciones específicas

Si algunas operaciones fallan pero otras funcionan, revisa la implementación del handler correspondiente en el servidor.

### No se reciben eventos

Si la prueba de eventos en tiempo real falla, verifica:

1. Que el sistema de eventos esté correctamente implementado
2. Que los eventos se estén disparando cuando corresponde
3. Que los eventos se estén enviando a los clientes conectados

## Notas Adicionales

- Las pruebas crean datos de prueba en el servidor (conversaciones, mensajes, etc.)
- Cada ejecución usa un ID de usuario único para evitar conflictos
- Las pruebas son idempotentes y pueden ejecutarse múltiples veces sin efectos secundarios
