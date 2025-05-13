@echo off
REM Script para desplegar la solución de rutas de API en el servidor (Windows)

echo === Desplegando solución de rutas de API ===
echo Este script ayuda a desplegar los cambios en las rutas de API en el servidor.
echo.

REM Verificar si git está instalado
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo X Error: Git no está instalado. Por favor, instala Git y vuelve a intentarlo.
    exit /b 1
)

REM Verificar si estamos en un repositorio git
if not exist ".git" (
    echo X Error: No estás en un repositorio Git. Por favor, ejecuta este script desde la raíz del repositorio.
    exit /b 1
)

REM Verificar si hay cambios sin confirmar
git status --porcelain > temp_status.txt
set /p GIT_STATUS=<temp_status.txt
del temp_status.txt

if not "%GIT_STATUS%"=="" (
    echo Advertencia: Hay cambios sin confirmar en el repositorio.
    echo Los siguientes archivos han sido modificados:
    git status --short
    
    set /p CONFIRM="¿Deseas continuar y confirmar estos cambios? (s/n): "
    if /i not "%CONFIRM%"=="s" (
        echo Operación cancelada.
        exit /b 0
    )
    
    REM Añadir los archivos modificados
    git add App/Api/conversations.py App/Api/messages.py Test/test_api_routes.js Test/API_ROUTES_FIX_README.md
    
    REM Confirmar los cambios
    git commit -m "Fix: Añadir soporte para rutas de API con y sin barra final"
    
    echo ✓ Cambios confirmados localmente.
) else (
    echo No hay cambios para confirmar.
)

REM Preguntar si desea subir los cambios
set /p PUSH="¿Deseas subir los cambios al repositorio remoto? (s/n): "
if /i "%PUSH%"=="s" (
    REM Obtener la rama actual
    for /f "tokens=*" %%a in ('git symbolic-ref --short HEAD') do set CURRENT_BRANCH=%%a
    
    REM Subir los cambios
    git push origin %CURRENT_BRANCH%
    
    if %ERRORLEVEL% equ 0 (
        echo ✓ Cambios subidos correctamente a la rama %CURRENT_BRANCH%.
        echo Si tu servidor está configurado para despliegue automático, los cambios se aplicarán pronto.
    ) else (
        echo X Error al subir los cambios. Por favor, verifica tu conexión y permisos.
        exit /b 1
    )
) else (
    echo Los cambios no se han subido al repositorio remoto.
)

echo.
echo === Pasos adicionales ===
echo 1. Si tu servidor no tiene despliegue automático, deberás desplegar manualmente la aplicación.
echo 2. Puedes probar los cambios ejecutando: node Test/test_api_routes.js
echo 3. Verifica que todas las rutas (con y sin barra final) funcionen correctamente.
echo.
echo ¡Listo! La solución de rutas de API ha sido desplegada.
