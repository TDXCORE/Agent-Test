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
            # Crear cliente HTTP con timeout configurado
            http_client = httpx.Client(timeout=REQUEST_TIMEOUT)
            
            # Crear cliente Supabase con el cliente HTTP personalizado
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY, http_client=http_client)
            logger.info("Cliente Supabase inicializado con timeout de 60 segundos")
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
        return MockTable()

class MockTable:
    """Tabla mock para cuando Supabase no está disponible"""
    
    def select(self, *args):
        return self
    
    def insert(self, *args):
        return self
    
    def update(self, *args):
        return self
    
    def delete(self, *args):
        return self
    
    def eq(self, *args):
        return self
    
    def order(self, *args, **kwargs):
        return self
    
    def execute(self):
        # Retornar un objeto con estructura similar a la respuesta de Supabase
        return MockResponse()

class MockResponse:
    """Respuesta mock para cuando Supabase no está disponible"""
    
    def __init__(self):
        self.data = []
