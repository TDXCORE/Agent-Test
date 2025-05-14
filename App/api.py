import os
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import dependencies
from App.DB.supabase_client import get_supabase_client

# Import API routers
from App.Api.conversations import router as conversations_router
from App.Api.messages import router as messages_router
from App.Api.users import router as users_router

# Import webhook handler
from App.Services.simple_webhook import app as webhook_app

# Create FastAPI app
app = FastAPI(
    title="Chat API",
    description="API for chat application using FastAPI and Supabase",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include API routers
app.include_router(conversations_router, prefix="/api/conversations", tags=["conversations"])
app.include_router(messages_router, prefix="/api/messages", tags=["messages"])
app.include_router(users_router, prefix="/api/users", tags=["users"])

# Mount the webhook app
# This will route all requests to /webhook to the webhook_app
from fastapi.middleware.wsgi import WSGIMiddleware
app.mount("/webhook", WSGIMiddleware(webhook_app))

@app.get("/")
async def root():
    return {"message": "Welcome to the Chat API"}

@app.get("/health-check", tags=["health"])
async def health_check():
    """
    Verifica el estado de las integraciones externas (WhatsApp API y Outlook)
    """
    health_data = {
        "timestamp": datetime.now().isoformat(),
        "status": "ok",
        "integrations": {}
    }
    
    # Verificar WhatsApp API
    try:
        from App.Services.whatsapp_api import WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID
        if WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID:
            health_data["integrations"]["whatsapp"] = {
                "status": "configured",
                "details": "WhatsApp credentials found"
            }
        else:
            health_data["integrations"]["whatsapp"] = {
                "status": "warning",
                "details": "WhatsApp credentials not found or incomplete"
            }
            health_data["status"] = "degraded"
    except Exception as e:
        health_data["integrations"]["whatsapp"] = {
            "status": "error",
            "details": str(e)
        }
        health_data["status"] = "degraded"
    
    # Verificar Outlook/Microsoft Graph
    try:
        from App.Services.outlook import get_access_token
        token, token_type = get_access_token()
        if token:
            health_data["integrations"]["outlook"] = {
                "status": "ok",
                "details": f"Connected using {token_type} authentication"
            }
        else:
            health_data["integrations"]["outlook"] = {
                "status": "error",
                "details": "Failed to obtain access token"
            }
            health_data["status"] = "degraded"
    except Exception as e:
        health_data["integrations"]["outlook"] = {
            "status": "error",
            "details": str(e)
        }
        health_data["status"] = "degraded"
    
    # Verificar base de datos Supabase
    try:
        supabase = get_supabase_client()
        # Consulta simple para verificar conexión
        response = supabase.table("users").select("count", "exact").limit(1).execute()
        health_data["integrations"]["database"] = {
            "status": "ok",
            "details": "Connected to Supabase"
        }
    except Exception as e:
        health_data["integrations"]["database"] = {
            "status": "error",
            "details": str(e)
        }
        health_data["status"] = "degraded"
    
    return health_data

@app.get("/health-dashboard", tags=["health"])
async def health_dashboard():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>API Health Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
            h1 { color: #333; }
            .dashboard { max-width: 800px; margin: 0 auto; }
            .status-card { 
                border: 1px solid #ddd; 
                border-radius: 4px; 
                padding: 15px; 
                margin-bottom: 15px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
            }
            .status-header { 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                margin-bottom: 10px; 
            }
            .status-title { font-weight: bold; font-size: 18px; }
            .status-indicator { 
                padding: 5px 10px; 
                border-radius: 4px; 
                font-weight: bold; 
            }
            .status-ok { background-color: #d4edda; color: #155724; }
            .status-error { background-color: #f8d7da; color: #721c24; }
            .status-details { color: #666; margin-top: 10px; }
            .refresh-button {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                margin-bottom: 20px;
            }
            .timestamp { color: #666; font-size: 14px; margin-bottom: 20px; }
            .endpoint-url { font-family: monospace; color: #666; }
            .response-data { 
                background-color: #f8f9fa; 
                padding: 10px; 
                border-radius: 4px; 
                font-family: monospace;
                white-space: pre-wrap;
                max-height: 200px;
                overflow-y: auto;
            }
        </style>
    </head>
    <body>
        <div class="dashboard">
            <h1>API Health Dashboard</h1>
            <button class="refresh-button" onclick="checkAllEndpoints()">Refresh All</button>
            <div id="timestamp" class="timestamp">Last updated: Never</div>
            
            <div id="endpoints-container"></div>
        </div>

        <script>
            // Definir los endpoints a verificar
            const endpoints = [
                {
                    name: "API Root",
                    url: "/",
                    method: "GET",
                    description: "Mensaje de bienvenida a la API"
                },
                {
                    name: "WhatsApp Webhook",
                    url: "/webhook",
                    method: "GET",
                    description: "Webhook para recibir mensajes de WhatsApp"
                },
                {
                    name: "Conversaciones",
                    url: "/api/conversations?user_id=test",
                    method: "GET",
                    description: "Gestión de conversaciones"
                },
                {
                    name: "Mensajes",
                    url: "/api/messages?conversation_id=test",
                    method: "GET",
                    description: "Gestión de mensajes"
                },
                {
                    name: "Usuarios",
                    url: "/api/users?phone=test",
                    method: "GET",
                    description: "Gestión de usuarios"
                },
                {
                    name: "Integraciones",
                    url: "/health-check",
                    method: "GET",
                    description: "Estado de integraciones externas (WhatsApp, Outlook, Supabase)"
                }
            ];

            // Función para verificar un endpoint
            async function checkEndpoint(endpoint, cardElement) {
                const statusHeader = cardElement.querySelector('.status-header');
                const statusIndicator = cardElement.querySelector('.status-indicator');
                const statusDetails = cardElement.querySelector('.status-details');
                
                try {
                    const startTime = performance.now();
                    const response = await fetch(endpoint.url);
                    const endTime = performance.now();
                    const responseTime = Math.round(endTime - startTime);
                    
                    let responseData;
                    try {
                        responseData = await response.json();
                    } catch (e) {
                        responseData = await response.text();
                    }
                    
                    // Actualizar indicador de estado
                    statusIndicator.className = 'status-indicator status-ok';
                    statusIndicator.textContent = 'OK';
                    
                    // Mostrar detalles
                    statusDetails.innerHTML = 
                        `<div>Status: ${response.status} ${response.statusText}</div>
                         <div>Response time: ${responseTime}ms</div>
                         <div class="response-data">${JSON.stringify(responseData, null, 2)}</div>`;
                } catch (error) {
                    // Actualizar indicador de estado
                    statusIndicator.className = 'status-indicator status-error';
                    statusIndicator.textContent = 'ERROR';
                    
                    // Mostrar detalles del error
                    statusDetails.innerHTML = `<div>Error: ${error.message}</div>`;
                }
            }

            // Función para crear tarjetas de estado para cada endpoint
            function createEndpointCards() {
                const container = document.getElementById('endpoints-container');
                container.innerHTML = '';
                
                endpoints.forEach(endpoint => {
                    const card = document.createElement('div');
                    card.className = 'status-card';
                    
                    card.innerHTML = `
                        <div class="status-header">
                            <div class="status-title">${endpoint.name}</div>
                            <div class="status-indicator">CHECKING...</div>
                        </div>
                        <div class="endpoint-url">${endpoint.method} ${endpoint.url}</div>
                        <div class="status-details">${endpoint.description}</div>
                        <button class="refresh-button" style="margin-top: 10px;" onclick="checkSingleEndpoint(${endpoints.indexOf(endpoint)})">Check</button>
                    `;
                    
                    container.appendChild(card);
                });
            }

            // Función para verificar un solo endpoint
            function checkSingleEndpoint(index) {
                const endpoint = endpoints[index];
                const cards = document.querySelectorAll('.status-card');
                const card = cards[index];
                
                checkEndpoint(endpoint, card);
            }

            // Función para verificar todos los endpoints
            function checkAllEndpoints() {
                document.getElementById('timestamp').textContent = 'Last updated: ' + new Date().toLocaleString();
                
                const cards = document.querySelectorAll('.status-card');
                
                endpoints.forEach((endpoint, index) => {
                    checkEndpoint(endpoint, cards[index]);
                });
            }

            // Inicializar la página
            document.addEventListener('DOMContentLoaded', () => {
                createEndpointCards();
                checkAllEndpoints();
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.on_event("startup")
async def startup_event():
    # Initialize Supabase client on startup
    logger.info("Initializing Supabase client")
    get_supabase_client()
    
    # Log successful initialization
    logger.info("API initialized successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("App.api:app", host="0.0.0.0", port=8000, reload=True)
