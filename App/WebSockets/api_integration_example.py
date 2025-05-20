"""
Ejemplo de cómo integrar WebSockets en el archivo api.py existente.
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="FullStackAgent API",
    description="API para la aplicación FullStackAgent",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar rutas API existentes
from App.Api.conversations import router as conversations_router
from App.Api.messages import router as messages_router
from App.Api.users import router as users_router

# Registrar rutas
app.include_router(conversations_router, prefix="/api/conversations", tags=["conversations"])
app.include_router(messages_router, prefix="/api/messages", tags=["messages"])
app.include_router(users_router, prefix="/api/users", tags=["users"])

# Importar e integrar WebSockets
from App.WebSockets.integration import integrate_websockets

# Integrar WebSockets con la aplicación
integrate_websockets()

# Ruta de estado
@app.get("/api/health")
async def health_check():
    """Verifica el estado de la API."""
    return {"status": "ok", "websockets_enabled": True}

# Punto de entrada para ejecución directa
if __name__ == "__main__":
    import uvicorn
    
    # Obtener puerto de variables de entorno o usar 8000 por defecto
    port = int(os.getenv("PORT", 8000))
    
    # Iniciar servidor
    uvicorn.run(
        "App.api:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
