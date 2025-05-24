# 🧪 WEBSOCKET ENHANCED DEBUG TEST SUITE

## 📋 Descripción

Suite mejorada de pruebas WebSocket con debugging avanzado, logging detallado y análisis completo de errores para identificar problemas con mayor precisión.

## 🆚 Diferencias con el Script Original

### Script Original (`test_new_handlers.py`)
- ✅ Pruebas básicas de todos los handlers
- ✅ Reporte de resultados simple
- ✅ Métricas básicas de rendimiento

### Script Mejorado (`test_new_handlers_enhanced.py`)
- 🚀 **Logging detallado con timestamps precisos**
- 🔍 **Stack traces completos para errores**
- 📊 **Métricas avanzadas de rendimiento**
- 🌐 **Información detallada de conexión WebSocket**
- 💾 **Guardado automático de logs en archivos**
- 🎯 **Validación de campos esperados vs recibidos**
- 📈 **Scores de validación de datos**
- 🔄 **Retry automático con backoff exponencial**
- 🖥️ **Información completa del sistema**
- 📋 **Análisis detallado de errores con categorización**

## 🚀 Nuevas Funcionalidades

### 1. **Logging Avanzado**
```python
# Logs se guardan automáticamente en:
App/WebSockets/logs/websocket_test_YYYYMMDD_HHMMSS.log

# Niveles de logging:
- DEBUG: Datos completos de request/response
- INFO: Información general de progreso
- WARNING: Advertencias y problemas menores
- ERROR: Errores con stack traces completos
```

### 2. **Métricas Detalladas**
```python
# Para cada prueba se captura:
- Tiempo de ejecución total
- Latencia de red
- Tiempo de procesamiento del servidor
- Uso de memoria y CPU
- Tamaño de datos transferidos
- Estado de conexión WebSocket
- Score de validación de datos (0-100%)
```

### 3. **Validación de Datos**
```python
# Validación automática de:
- Campos esperados vs recibidos
- Campos faltantes
- Campos inesperados
- Estructura de respuesta
- Códigos de estado HTTP equivalentes
```

### 4. **Análisis de Errores**
```python
# Para cada error se registra:
- Stack trace completo
- Timestamp exacto
- Información de conexión
- Métricas de rendimiento
- Categorización del error
- Sugerencias de solución
```

## 📁 Estructura de Archivos

```
App/WebSockets/
├── test_new_handlers.py              # Script original
├── test_new_handlers_enhanced.py     # Script mejorado
├── logs/                             # Directorio de logs (auto-creado)
│   └── websocket_test_YYYYMMDD_HHMMSS.log
└── README_ENHANCED_TESTING.md        # Esta documentación
```

## 🔧 Uso

### Ejecutar Script Mejorado
```bash
# Desde el directorio raíz del proyecto
python App/WebSockets/test_new_handlers_enhanced.py
```

### Ejecutar Script Original (para comparación)
```bash
python App/WebSockets/test_new_handlers.py
```

## 📊 Ejemplo de Output Mejorado

```
🧪 WEBSOCKET ENHANCED DEBUG TEST SUITE
=====================================
🚀 Iniciando suite mejorada con debugging avanzado...
📁 Los logs se guardarán en: App/WebSockets/logs/websocket_test_20240524_180530.log

🖥️  INFORMACIÓN DEL SISTEMA
============================
Sistema Operativo: Windows 11
Arquitectura: AMD64
Python: 3.11.5
Memoria Total: 16.0 GB
CPU Cores: 8

🔌 Intento de conexión WebSocket 1/3
✅ Conexión WebSocket establecida en 45.2ms
📨 Mensaje de bienvenida recibido

👥 === TESTING USERS HANDLER (ENHANCED) ===
🧪 INICIANDO PRUEBA: users.get_all_users
📤 Mensaje enviado en 2.1ms
📥 Respuesta recibida en 156.3ms
✅ Análisis completado - Success: True
📊 Validation score: 100.0%
✅ get_all_users - 158.4ms - Score: 100.0%

📊 REPORTE COMPLETO ENHANCED
============================
📈 RESUMEN EJECUTIVO ENHANCED:
│ Total Handlers Probados: 7
│ Total Funciones Probadas: 42
│ Pruebas Exitosas: 38/42 (90.5%)
│ Pruebas Fallidas: 4/42 (9.5%)
│ Promedio Score Validación: 87.3%
│ Total Datos Transferidos: 45.2 KB enviados, 123.8 KB recibidos

❌ ANÁLISIS DETALLADO DE ERRORES (4 errores encontrados):
🔍 ERROR #1: leads.get_lead_with_complete_data
   📋 Mensaje: Lead not found with ID: uuid-test
   🕐 Timestamp: 2024-05-24T18:05:45.123456
   ⏱️ Tiempo ejecución: 234.5ms
   🌐 HTTP equivalente: 404
   📋 Campos faltantes: ['lead']
```

## 🎯 Casos de Uso

### 1. **Debugging de Errores**
- Identifica exactamente dónde y cuándo ocurren los errores
- Proporciona stack traces completos
- Muestra el estado del sistema en el momento del error

### 2. **Optimización de Rendimiento**
- Identifica funciones lentas
- Analiza uso de recursos
- Compara tiempos de respuesta

### 3. **Validación de API**
- Verifica que las respuestas tengan la estructura esperada
- Identifica campos faltantes o inesperados
- Valida tipos de datos

### 4. **Monitoreo de Conexiones**
- Rastrea el estado de conexiones WebSocket
- Identifica problemas de red
- Monitorea reconexiones automáticas

## 🔧 Configuración Avanzada

### Modificar Timeouts
```python
# En el archivo test_new_handlers_enhanced.py
# Línea ~280: timeout para conexión WebSocket
websocket = await asyncio.wait_for(websockets.connect(WEBSOCKET_URL), timeout=10.0)

# Línea ~350: timeout para respuestas
response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
```

### Cambiar Nivel de Logging
```python
# En la función setup_logging() línea ~35
logging.basicConfig(
    level=logging.DEBUG,  # Cambiar a INFO, WARNING, ERROR según necesidad
    ...
)
```

### Personalizar Validaciones
```python
# En get_expected_fields() línea ~500
# Agregar o modificar campos esperados para cada función
```

## 📈 Métricas Disponibles

### Por Prueba Individual
- `execution_time_ms`: Tiempo total de ejecución
- `network_latency_ms`: Latencia de red
- `server_processing_time_ms`: Tiempo de procesamiento del servidor
- `data_validation_score`: Score de validación (0-100%)
- `request_size_bytes` / `response_size_bytes`: Tamaño de datos
- `records_processed`: Número de registros procesados

### Globales
- `total_connections`: Total de conexiones WebSocket
- `failed_connections`: Conexiones fallidas
- `total_bytes_sent` / `total_bytes_received`: Datos transferidos
- `avg_response_time`: Tiempo promedio de respuesta
- `success_rate`: Tasa de éxito general

## 🚨 Solución de Problemas

### Error: "No se pudo iniciar el servidor"
```bash
# Iniciar manualmente el servidor
uvicorn App.api:app --host 0.0.0.0 --port 8000
```

### Error: "No se pudo establecer conexión WebSocket"
1. Verificar que el servidor esté ejecutándose
2. Comprobar que el puerto 8000 esté disponible
3. Revisar logs para errores de conexión

### Logs no se guardan
1. Verificar permisos de escritura en `App/WebSockets/logs/`
2. El directorio se crea automáticamente si no existe

## 📝 Próximas Mejoras

- [ ] Integración con sistemas de monitoreo (Prometheus, Grafana)
- [ ] Exportación de métricas a formatos estándar (JSON, CSV)
- [ ] Dashboard web en tiempo real
- [ ] Alertas automáticas por email/Slack
- [ ] Comparación histórica de rendimiento
- [ ] Tests de carga y estrés
- [ ] Integración con CI/CD pipelines

---

**Creado por:** Sistema de Testing Avanzado WebSocket  
**Fecha:** Mayo 2024  
**Versión:** 1.0 Enhanced
