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
app.mount("/webhook", WSGIMiddleware(webhook_app), name="webhook")
logger.info("Webhook app montada en /webhook")

@app.get("/")
async def root():
    return {"message": "Welcome to the Chat API"}

@app.get("/health-check", tags=["health"])
async def health_check():
    """
    Verifica el estado de las integraciones externas (WhatsApp API y Outlook)
    y proporciona datos de prueba para los endpoints
    """
    health_data = {
        "timestamp": datetime.now().isoformat(),
        "status": "ok",
        "integrations": {},
        "test_data": {}  # Aquí almacenaremos IDs válidos para pruebas
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
        # Consulta simple para verificar conexión (sin usar 'exact')
        response = supabase.table("users").select("*").limit(1).execute()
        health_data["integrations"]["database"] = {
            "status": "ok",
            "details": "Connected to Supabase"
        }
        
        # Obtener datos de prueba de la base de datos
        try:
            # Obtener un usuario válido
            user_response = supabase.table("users").select("id").limit(1).execute()
            if user_response.data and len(user_response.data) > 0:
                user_id = user_response.data[0]["id"]
                health_data["test_data"]["user_id"] = user_id
                
                # Obtener una conversación válida para este usuario
                conv_response = supabase.table("conversations").select("id").eq("user_id", user_id).limit(1).execute()
                if conv_response.data and len(conv_response.data) > 0:
                    conv_id = conv_response.data[0]["id"]
                    health_data["test_data"]["conversation_id"] = conv_id
                    
                    # Obtener un mensaje válido para esta conversación
                    msg_response = supabase.table("messages").select("id").eq("conversation_id", conv_id).limit(1).execute()
                    if msg_response.data and len(msg_response.data) > 0:
                        msg_id = msg_response.data[0]["id"]
                        health_data["test_data"]["message_id"] = msg_id
        except Exception as e:
            health_data["test_data"]["error"] = str(e)
            
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
            .status-warning { background-color: #fff3cd; color: #856404; }
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
            // Almacenar datos de prueba
            let testData = {};

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
                    url: "/webhook?hub.mode=subscribe&hub.verify_token=8a4c9e2f7b3d1a5c8e4f2a169c7e5e3f&hub.challenge=test",
                    method: "GET",
                    description: "Verificación del webhook de WhatsApp"
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
                    url: "/api/users",
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

            // Función para obtener datos de prueba
            async function fetchTestData() {
                try {
                    const response = await fetch('/health-check');
                    const data = await response.json();
                    
                    if (data.test_data) {
                        testData = data.test_data;
                        console.log("Datos de prueba obtenidos:", testData);
                    }
                    
                    // Una vez que tenemos los datos, actualizar las URLs de los endpoints
                    updateEndpointUrls();
                } catch (error) {
                    console.error("Error al obtener datos de prueba:", error);
                }
            }

            // Función para actualizar las URLs de los endpoints con datos reales
            function updateEndpointUrls() {
                endpoints.forEach(endpoint => {
                    if (endpoint.name === "Conversaciones" && testData.user_id) {
                        endpoint.url = `/api/conversations?user_id=${testData.user_id}`;
                    } else if (endpoint.name === "Mensajes" && testData.conversation_id) {
                        endpoint.url = `/api/messages?conversation_id=${testData.conversation_id}`;
                    }
                });
                
                // Recrear las tarjetas con las nuevas URLs
                createEndpointCards();
            }

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
                    
                    // Determinar el estado basado en el código de respuesta y el contenido
                    let statusClass = 'status-ok';
                    let statusText = 'OK';
                    
                    // Verificar códigos de error
                    if (response.status >= 400 && response.status < 500) {
                        statusClass = 'status-warning';
                        statusText = 'WARNING';
                    } else if (response.status >= 500) {
                        statusClass = 'status-error';
                        statusText = 'ERROR';
                    }
                    
                    // Para el endpoint de integraciones, verificar el estado interno
                    if (endpoint.name === "Integraciones" && responseData.status === "degraded") {
                        statusClass = 'status-warning';
                        statusText = 'DEGRADED';
                    }
                    
                    // Verificar si hay errores en la respuesta
                    if (typeof responseData === 'object' && responseData !== null) {
                        if (responseData.detail && responseData.detail.includes("error")) {
                            statusClass = 'status-error';
                            statusText = 'ERROR';
                        }
                    }
                    
                    // Actualizar indicador de estado
                    statusIndicator.className = `status-indicator ${statusClass}`;
                    statusIndicator.textContent = statusText;
                    
                    // Mostrar detalles
                    statusDetails.innerHTML = 
                        `<div>Status: ${response.status}</div>
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
            document.addEventListener('DOMContentLoaded', async () => {
                // Primero obtener los datos de prueba
                await fetchTestData();
                
                // Luego verificar todos los endpoints
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
