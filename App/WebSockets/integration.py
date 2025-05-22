"""
Integración del módulo WebSockets con la aplicación principal.
"""

import logging
from fastapi import FastAPI
from typing import Dict, Any, Optional, List

from .main import init_websockets

logger = logging.getLogger(__name__)

def integrate_websockets(app: FastAPI):
    """
    Integra el módulo WebSockets con la aplicación principal.
    
    Esta función debe ser llamada desde el punto de entrada principal
    de la aplicación (App/api.py) para inicializar los WebSockets.
    """
    # Inicializar WebSockets en la aplicación FastAPI
    init_websockets(app)
    
    logger.info("Módulo WebSockets integrado con la aplicación principal")

# Ejemplo de cómo integrar en App/api.py:
"""
from fastapi import FastAPI
from App.WebSockets.integration import integrate_websockets

app = FastAPI()

# Configurar rutas y dependencias...

# Integrar WebSockets
integrate_websockets(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
