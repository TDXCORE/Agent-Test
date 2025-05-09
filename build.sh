#!/bin/bash

# Script de construcción para Render

# Instalar dependencias
echo "Instalando dependencias..."
pip install -r requirements.txt

# Verificar instalación
echo "Verificando instalación..."
pip list

echo "Construcción completada."
