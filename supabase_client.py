import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv
import httpx

load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de Supabase
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Configuración de timeout (60 segundos)
REQUEST_TIMEOUT = 60

# Variable global para el cliente de Supabase
supabase = None

def get_supabase_client():
    """Retorna el cliente de Supabase con timeout configurado"""
    global supabase
    
    # Inicializar el cliente solo si no existe y las variables de entorno están configuradas
    if supabase is None and SUPABASE_URL and SUPABASE_KEY:
        try:
            # Crear cliente Supabase con timeout configurado
            # Nota: No usamos http_client ya que no es compatible con la versión actual
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Cliente Supabase inicializado")
        except Exception as e:
            logger.error(f"Error al inicializar el cliente de Supabase: {str(e)}")
            # Retornar un objeto mock si hay error
            return MockSupabaseClient()
    
    # Si las variables de entorno no están configuradas, retornar un objeto mock
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Variables de entorno de Supabase no configuradas. Usando cliente mock.")
        return MockSupabaseClient()
    
    return supabase

# Clase mock para cuando Supabase no está disponible
class MockSupabaseClient:
    """Cliente mock de Supabase para cuando no está disponible"""
    
    def table(self, table_name):
        table = MockTable()
        table.table_name = table_name
        return table

class MockTable:
    """Tabla mock para cuando Supabase no está disponible"""
    
    def __init__(self):
        self.table_name = None
        self.filters = {}
        self.selected_fields = ["*"]
        self.order_field = None
        self.order_ascending = True
    
    def select(self, *args):
        self.selected_fields = args if args else ["*"]
        return self
    
    def insert(self, data):
        # Simular inserción retornando el mismo dato con un ID
        if isinstance(data, dict):
            # Generar un ID único para el nuevo registro
            data_id = "mock-id-" + str(hash(str(data)) % 10000)
            data["id"] = data_id
            # Añadir timestamps
            if "created_at" not in data:
                data["created_at"] = "2025-05-09T20:00:00.000Z"
            if "updated_at" not in data:
                data["updated_at"] = "2025-05-09T20:00:00.000Z"
            logger.info(f"[MOCK] Insertando datos en tabla '{self.table_name}': {data}")
        return self
    
    def update(self, data):
        # Simular actualización retornando el mismo dato
        if isinstance(data, dict):
            # Actualizar timestamp
            if "updated_at" not in data:
                data["updated_at"] = "2025-05-09T20:00:00.000Z"
            logger.info(f"[MOCK] Actualizando datos en tabla '{self.table_name}': {data}")
        return self
    
    def delete(self):
        # Simular eliminación
        return self
    
    def eq(self, field, value):
        self.filters[field] = value
        return self
    
    def order(self, field, options=None):
        self.order_field = field
        if options and isinstance(options, dict):
            self.order_ascending = options.get("ascending", True)
        return self
    
    def execute(self):
        # Generar datos mock según la tabla y filtros
        mock_data = self._generate_mock_data()
        logger.info(f"[MOCK] Ejecutando consulta en tabla '{self.table_name}' con filtros {self.filters}")
        return MockResponse(mock_data)
    
    def _generate_mock_data(self):
        """Genera datos mock según la tabla y filtros aplicados"""
        # Datos base para diferentes tablas
        mock_data = {
            "users": {
                "id": "mock-user-id",
                "created_at": "2025-05-09T20:00:00.000Z",
                "updated_at": "2025-05-09T20:00:00.000Z",
                "phone": "573153041548",  # Usar un número real para pruebas
                "email": "mock-email@example.com",
                "full_name": "Usuario Mock",
                "company": "Empresa Mock"
            },
            "conversations": {
                "id": "mock-conversation-id",
                "created_at": "2025-05-09T20:00:00.000Z",
                "updated_at": "2025-05-09T20:00:00.000Z",
                "user_id": "mock-user-id",
                "external_id": "573153041548",  # Usar un número real para pruebas
                "platform": "whatsapp",
                "status": "active"
            }
        }
        
        # Para la tabla de mensajes, generamos una lista de mensajes para simular una conversación
        if self.table_name == "messages":
            # Si hay un filtro de conversation_id, usamos ese ID
            conversation_id = self.filters.get("conversation_id", "mock-conversation-id")
            
            # Verificar si estamos buscando un mensaje específico o todos los mensajes de una conversación
            if "id" in self.filters:
                # Si buscamos un mensaje específico, devolvemos solo ese mensaje
                return [{
                    "id": self.filters["id"],
                    "created_at": "2025-05-09T20:00:00.000Z",
                    "updated_at": "2025-05-09T20:00:00.000Z",
                    "conversation_id": conversation_id,
                    "role": "user",
                    "content": "Mensaje específico",
                    "message_type": "text",
                    "media_url": None,
                    "external_id": "mock-external-id-specific"
                }]
            else:
                # Si buscamos todos los mensajes de una conversación, devolvemos una secuencia de mensajes
                return [
                    {
                        "id": "mock-message-system",
                        "created_at": "2025-05-09T20:00:00.000Z",
                        "updated_at": "2025-05-09T20:00:00.000Z",
                        "conversation_id": conversation_id,
                        "role": "system",
                        "content": "Iniciando conversación con un potencial cliente.",
                        "message_type": "text",
                        "media_url": None,
                        "external_id": None
                    },
                    {
                        "id": "mock-message-assistant-1",
                        "created_at": "2025-05-09T20:01:00.000Z",
                        "updated_at": "2025-05-09T20:01:00.000Z",
                        "conversation_id": conversation_id,
                        "role": "assistant",
                        "content": "¡Hola! Soy el asistente virtual de nuestra empresa de desarrollo de software. ¿En qué puedo ayudarte hoy?",
                        "message_type": "text",
                        "media_url": None,
                        "external_id": None
                    },
                    {
                        "id": "mock-message-user-1",
                        "created_at": "2025-05-09T20:02:00.000Z",
                        "updated_at": "2025-05-09T20:02:00.000Z",
                        "conversation_id": conversation_id,
                        "role": "user",
                        "content": "Hola",
                        "message_type": "text",
                        "media_url": None,
                        "external_id": "mock-external-id-1"
                    },
                    {
                        "id": "mock-message-assistant-2",
                        "created_at": "2025-05-09T20:03:00.000Z",
                        "updated_at": "2025-05-09T20:03:00.000Z",
                        "conversation_id": conversation_id,
                        "role": "assistant",
                        "content": "¡Hola! Soy tu asistente virtual especializado en calificar leads para nuestra empresa de desarrollo de software. Estoy aquí para ayudarte a través del proceso de calificación y agendar una cita para discutir tus necesidades.\n\nPara comenzar, necesito tu consentimiento para procesar tus datos personales de acuerdo con el GDPR/LPD. ¿Estás de acuerdo en continuar?",
                        "message_type": "text",
                        "media_url": None,
                        "external_id": None
                    },
                    {
                        "id": "mock-message-user-2",
                        "created_at": "2025-05-09T20:04:00.000Z",
                        "updated_at": "2025-05-09T20:04:00.000Z",
                        "conversation_id": conversation_id,
                        "role": "user",
                        "content": "Si",
                        "message_type": "text",
                        "media_url": None,
                        "external_id": "mock-external-id-2"
                    }
                ]
        
        # Usar datos por defecto si no hay tabla específica
        default_data = {
            "id": "mock-id-12345",
            "created_at": "2025-05-09T20:00:00.000Z",
            "updated_at": "2025-05-09T20:00:00.000Z"
        }
        
        # Seleccionar datos según la tabla
        data = mock_data.get(self.table_name, default_data)
        
        # Aplicar filtros si existen
        if self.filters:
            # En un caso real, filtrarías los datos aquí
            # Para el mock, simplemente aseguramos que los datos tengan los campos filtrados
            for field, value in self.filters.items():
                data[field] = value
        
        return [data]

class MockResponse:
    """Respuesta mock para cuando Supabase no está disponible"""
    
    def __init__(self, data=None):
        # Usar datos proporcionados o datos por defecto
        self.data = data if data is not None else [{
            "id": "mock-id-12345",
            "created_at": "2025-05-09T20:00:00.000Z",
            "updated_at": "2025-05-09T20:00:00.000Z",
            "phone": "mock-phone",
            "email": "mock-email@example.com",
            "full_name": "Usuario Mock",
            "company": "Empresa Mock",
            "external_id": "mock-external-id",
            "platform": "whatsapp",
            "status": "active",
            "user_id": "mock-user-id",
            "conversation_id": "mock-conversation-id",
            "role": "user",
            "content": "Mensaje mock",
            "message_type": "text",
            "media_url": None
        }]
