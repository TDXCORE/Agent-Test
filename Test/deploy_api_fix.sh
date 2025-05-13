#!/bin/bash
# Script para desplegar la solución de rutas de API en el servidor

echo "=== Desplegando solución de rutas de API ==="
echo "Este script ayuda a desplegar los cambios en las rutas de API en el servidor."
echo ""

# Verificar si git está instalado
if ! command -v git &> /dev/null; then
    echo "❌ Error: Git no está instalado. Por favor, instala Git y vuelve a intentarlo."
    exit 1
fi

# Verificar si estamos en un repositorio git
if [ ! -d ".git" ]; then
    echo "❌ Error: No estás en un repositorio Git. Por favor, ejecuta este script desde la raíz del repositorio."
    exit 1
fi

# Verificar si hay cambios sin confirmar
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️ Advertencia: Hay cambios sin confirmar en el repositorio."
    echo "Los siguientes archivos han sido modificados:"
    git status --short
    
    read -p "¿Deseas continuar y confirmar estos cambios? (s/n): " confirm
    if [ "$confirm" != "s" ]; then
        echo "Operación cancelada."
        exit 0
    fi
    
    # Añadir los archivos modificados
    git add App/Api/conversations.py App/Api/messages.py Test/test_api_routes.js Test/API_ROUTES_FIX_README.md
    
    # Confirmar los cambios
    git commit -m "Fix: Añadir soporte para rutas de API con y sin barra final"
    
    echo "✅ Cambios confirmados localmente."
else
    echo "No hay cambios para confirmar."
fi

# Preguntar si desea subir los cambios
read -p "¿Deseas subir los cambios al repositorio remoto? (s/n): " push
if [ "$push" = "s" ]; then
    # Obtener la rama actual
    current_branch=$(git symbolic-ref --short HEAD)
    
    # Subir los cambios
    git push origin $current_branch
    
    if [ $? -eq 0 ]; then
        echo "✅ Cambios subidos correctamente a la rama $current_branch."
        echo "Si tu servidor está configurado para despliegue automático, los cambios se aplicarán pronto."
    else
        echo "❌ Error al subir los cambios. Por favor, verifica tu conexión y permisos."
        exit 1
    fi
else
    echo "Los cambios no se han subido al repositorio remoto."
fi

echo ""
echo "=== Pasos adicionales ==="
echo "1. Si tu servidor no tiene despliegue automático, deberás desplegar manualmente la aplicación."
echo "2. Puedes probar los cambios ejecutando: node Test/test_api_routes.js"
echo "3. Verifica que todas las rutas (con y sin barra final) funcionen correctamente."
echo ""
echo "¡Listo! La solución de rutas de API ha sido desplegada."
