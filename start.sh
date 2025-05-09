#!/bin/bash

# Script de inicio para Render

# Iniciar la aplicación con gunicorn
echo "Iniciando aplicación con gunicorn..."
gunicorn simple_app:app --timeout 120
