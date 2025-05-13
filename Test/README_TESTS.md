# Pruebas de Conexión a Supabase y Almacenamiento del Agente

Este directorio contiene scripts para verificar la conexión a Supabase y el almacenamiento de datos del agente de calificación de leads.

## Descripción de los Scripts

### 1. `test_supabase_connection.py`

Este script verifica la conexión básica a Supabase y realiza operaciones CRUD (Crear, Leer, Actualizar, Eliminar) para asegurarse de que la base de datos funciona correctamente.

**Funciones principales:**
- `test_supabase_connection()`: Prueba la conexión básica a Supabase
- `test_crud_operations()`: Prueba operaciones CRUD completas en Supabase

### 2. `test_agent_storage.py`

Este script simula una conversación con el agente y verifica que los datos se están guardando correctamente en la base de datos.

**Funciones principales:**
- `test_agent_storage()`: Prueba que el agente guarda correctamente la información en la base de datos

### 3. `run_tests.py`

Este script ejecuta todas las pruebas y muestra un resumen de los resultados.

## Requisitos Previos

Antes de ejecutar las pruebas, asegúrate de tener:

1. Python 3.8 o superior instalado
2. Las dependencias necesarias instaladas:
   ```
   pip install supabase python-dotenv
   ```
3. Un archivo `.env` en la raíz del proyecto con las siguientes variables:
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://tu-proyecto.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=tu-clave-de-servicio
   ```

## Cómo Ejecutar las Pruebas

### Ejecutar todas las pruebas

Para ejecutar todas las pruebas y ver un resumen de los resultados:

```bash
python Test/run_tests.py
```

### Ejecutar pruebas individuales

Para ejecutar solo la prueba de conexión a Supabase:

```bash
python Test/test_supabase_connection.py
```

Para ejecutar solo la prueba de almacenamiento del agente:

```bash
python Test/test_agent_storage.py
```

## Interpretación de los Resultados

### Prueba de Conexión a Supabase

- ✅ **Exitosa**: La conexión a Supabase funciona correctamente y se pueden realizar operaciones CRUD.
- ❌ **Fallida**: Hay problemas con la conexión a Supabase. Verifica las variables de entorno y la configuración de Supabase.

### Prueba de Almacenamiento del Agente

- ✅ **Exitosa**: El agente está guardando correctamente la información en la base de datos.
- ❌ **Fallida**: El agente no está guardando la información en la base de datos. Verifica la configuración del agente y las funciones de almacenamiento.

## Solución de Problemas

### Si la conexión a Supabase falla:

1. Verifica que las variables de entorno estén configuradas correctamente en el archivo `.env`.
2. Asegúrate de que el proyecto de Supabase exista y esté accesible.
3. Verifica que la clave de servicio sea válida y tenga los permisos necesarios.
4. Comprueba si estás usando el cliente mock en lugar del real (esto ocurre cuando las variables de entorno no están configuradas).

### Si las operaciones CRUD fallan:

1. Verifica que las políticas de seguridad de Supabase permitan las operaciones necesarias.
2. Asegúrate de que la estructura de las tablas en Supabase coincida con la esperada.
3. Comprueba que la clave de servicio tenga los permisos necesarios para realizar operaciones CRUD.

### Si el almacenamiento del agente falla:

1. Verifica que el agente esté configurado correctamente para usar Supabase.
2. Asegúrate de que las funciones del agente estén llamando a las funciones de `db_operations.py`.
3. Comprueba si hay errores en las funciones de `db_operations.py` que impidan guardar la información.
4. Verifica que la estructura de las tablas en Supabase coincida con la esperada por el agente.

## Estructura de Tablas Esperada

Para que las pruebas funcionen correctamente, Supabase debe tener las siguientes tablas con la estructura adecuada:

1. `users`: Almacena información de los usuarios
2. `conversations`: Almacena conversaciones activas
3. `lead_qualification`: Almacena el estado del proceso de calificación
4. `bant_data`: Almacena información BANT
5. `requirements`: Almacena requerimientos técnicos
6. `features`: Almacena características específicas
7. `integrations`: Almacena integraciones necesarias
8. `meetings`: Almacena reuniones agendadas

## Notas Adicionales

- Las pruebas utilizan IDs únicos para evitar conflictos con datos existentes.
- Si una prueba falla, las siguientes pueden no ejecutarse para evitar errores en cascada.
- El script `test_agent_storage.py` crea datos manualmente si es necesario para continuar con las pruebas.
