#!/bin/bash

# Script de inicio para Render

# Iniciar la aplicación con gunicorn
echo "Iniciando aplicación con gunicorn..."
gunicorn whatsapp_api:app --timeout 120
