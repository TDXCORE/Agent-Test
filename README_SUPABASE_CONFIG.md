# Configuración de Supabase en Render

Este documento explica cómo configurar las variables de entorno de Supabase en Render para que la aplicación funcione correctamente.

## Variables de Entorno Requeridas

Para que la aplicación se conecte correctamente a Supabase, necesitas configurar las siguientes variables de entorno en Render:

```
NEXT_PUBLIC_SUPABASE_URL=https://tu-proyecto.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=tu-clave-anon-publica
SUPABASE_SERVICE_ROLE_KEY=tu-clave-service-role
```

## Pasos para Configurar

1. Inicia sesión en [Render](https://dashboard.render.com/)
2. Navega a tu servicio web
3. Ve a la pestaña "Environment"
4. Añade las siguientes variables de entorno:
   - `NEXT_PUBLIC_SUPABASE_URL`: La URL de tu proyecto Supabase (ej: https://tu-proyecto.supabase.co)
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`: La clave anónima pública de tu proyecto Supabase
   - `SUPABASE_SERVICE_ROLE_KEY`: La clave de rol de servicio de tu proyecto Supabase
5. Haz clic en "Save Changes"
6. Reinicia tu servicio para aplicar los cambios

## Obtener las Claves de Supabase

Para obtener estas claves:

1. Inicia sesión en [Supabase](https://app.supabase.io/)
2. Selecciona tu proyecto
3. Ve a "Settings" > "API"
4. En la sección "Project API keys", encontrarás:
   - `URL`: Es tu `NEXT_PUBLIC_SUPABASE_URL`
   - `anon public`: Es tu `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `service_role`: Es tu `SUPABASE_SERVICE_ROLE_KEY`

## Verificación

Para verificar que la configuración es correcta:

1. Despliega tu aplicación en Render
2. Revisa los logs para confirmar que no aparece el mensaje "Variables de entorno de Supabase no configuradas. Usando cliente mock."
3. Prueba enviar un mensaje a través de WhatsApp y verifica que se procese correctamente

## Solución de Problemas

Si sigues viendo el mensaje "Variables de entorno de Supabase no configuradas. Usando cliente mock." en los logs:

1. Verifica que has añadido todas las variables de entorno correctamente
2. Asegúrate de que has reiniciado el servicio después de añadir las variables
3. Comprueba que no hay errores de tipografía en los nombres de las variables

Si el error persiste, revisa los logs completos para ver si hay algún otro error relacionado con la conexión a Supabase.
