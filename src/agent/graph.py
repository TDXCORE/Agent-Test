"""
Configuración del grafo para LangGraph.
Este archivo define el grafo que se utilizará cuando se ejecute el agente con LangGraph.
"""

import sys
import os

# Añadir el directorio raíz al path para poder importar desde main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import create_lead_qualification_agent

# Crear el agente que será utilizado por LangGraph
graph = create_lead_qualification_agent()
