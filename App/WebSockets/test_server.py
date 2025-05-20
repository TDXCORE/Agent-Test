"""
Servidor de prueba para WebSockets.
Este script inicia un servidor FastAPI con WebSockets habilitados para pruebas.
"""

import asyncio
import logging
import sys
import os
import uvicorn
from fastapi import FastAPI

# Añadir directorio raíz al path para poder importar App
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="WebSockets Test Server",
    description="Servidor de prueba para WebSockets",
    version="1.0.0"
)

# Importar e inicializar WebSockets
from App.WebSockets.main import init_websockets

# Inicializar WebSockets en la aplicación
init_websockets(app)

# Ruta de estado
@app.get("/")
async def root():
    """Ruta raíz para verificar que el servidor está funcionando."""
    return {"status": "ok", "message": "Servidor de prueba para WebSockets funcionando"}

@app.get("/health")
async def health_check():
    """Verifica el estado del servidor."""
    return {"status": "ok", "websockets_enabled": True}

# Punto de entrada para ejecución directa
if __name__ == "__main__":
    logger.info("Iniciando servidor de prueba para WebSockets en http://localhost:8000")
    logger.info("Endpoint WebSocket disponible en ws://localhost:8000/ws")
    logger.info("Presiona Ctrl+C para detener el servidor")
    
    # Iniciar servidor
    uvicorn.run(
        "App.WebSockets.test_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
