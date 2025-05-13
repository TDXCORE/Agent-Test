# Test/test_supabase_connection.py

import os
import sys
import logging
from dotenv import load_dotenv
from supabase import create_client
import uuid

# Añadir el directorio raíz al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Obtener credenciales
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def test_supabase_connection():
    """Prueba la conexión básica a Supabase"""
    
    # Verificar que las credenciales existen
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("❌ Credenciales de Supabase no configuradas")
        logger.error(f"NEXT_PUBLIC_SUPABASE_URL: {'Configurado' if SUPABASE_URL else 'No configurado'}")
        logger.error(f"SUPABASE_SERVICE_ROLE_KEY: {'Configurado' if SUPABASE_KEY else 'No configurado'}")
        return False
    
    try:
        # Intentar crear el cliente
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Cliente Supabase creado correctamente")
        
        # Probar una operación de lectura simple
        response = supabase.table("users").select("*").limit(1).execute()
        logger.info(f"✅ Operación SELECT exitosa. Respuesta: {response.data}")
        
        # Verificar si estamos usando el cliente real o el mock
        is_mock = hasattr(supabase, "__class__") and supabase.__class__.__name__ == "MockSupabaseClient"
        if is_mock:
            logger.warning("⚠️ Estás usando el cliente MOCK de Supabase, no el real")
            return False
        
        return True
    except Exception as e:
        logger.error(f"❌ Error al conectar con Supabase: {str(e)}")
        import traceback
        logger.error(f"Traza completa: {traceback.format_exc()}")
        return False

def test_crud_operations():
    """Prueba operaciones CRUD completas en Supabase"""
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("❌ Credenciales de Supabase no configuradas")
        return False
    
    try:
        # Crear cliente
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Generar datos de prueba
        test_id = str(uuid.uuid4())
        test_user = {
            "full_name": f"Usuario Prueba {test_id}",
            "email": f"test_{test_id}@example.com",
            "phone": f"+1{test_id[-10:]}",
            "company": "Empresa de Prueba"
        }
        
        # 1. CREATE - Insertar usuario de prueba
        logger.info(f"Insertando usuario de prueba: {test_user['full_name']}")
        insert_response = supabase.table("users").insert(test_user).execute()
        
        if not insert_response.data:
            logger.error("❌ Error al insertar usuario de prueba")
            return False
        
        created_user = insert_response.data[0]
        user_id = created_user["id"]
        logger.info(f"✅ Usuario creado con ID: {user_id}")
        
        # 2. READ - Leer el usuario creado
        read_response = supabase.table("users").select("*").eq("id", user_id).execute()
        
        if not read_response.data or len(read_response.data) == 0:
            logger.error("❌ Error al leer usuario de prueba")
            return False
        
        logger.info(f"✅ Usuario leído correctamente: {read_response.data[0]['full_name']}")
        
        # 3. UPDATE - Actualizar el usuario
        update_data = {"company": "Empresa Actualizada"}
        update_response = supabase.table("users").update(update_data).eq("id", user_id).execute()
        
        if not update_response.data:
            logger.error("❌ Error al actualizar usuario de prueba")
            return False
        
        logger.info(f"✅ Usuario actualizado correctamente: {update_response.data[0]['company']}")
        
        # 4. DELETE - Eliminar el usuario de prueba
        delete_response = supabase.table("users").delete().eq("id", user_id).execute()
        
        if not delete_response.data:
            logger.error("❌ Error al eliminar usuario de prueba")
            return False
        
        logger.info(f"✅ Usuario eliminado correctamente")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error en operaciones CRUD: {str(e)}")
        import traceback
        logger.error(f"Traza completa: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("\n=== PRUEBA DE CONEXIÓN A SUPABASE ===\n")
    
    connection_success = test_supabase_connection()
    print(f"\nPrueba de conexión: {'✅ EXITOSA' if connection_success else '❌ FALLIDA'}")
    
    if connection_success:
        print("\n=== PRUEBA DE OPERACIONES CRUD ===\n")
        crud_success = test_crud_operations()
        print(f"\nPrueba de operaciones CRUD: {'✅ EXITOSA' if crud_success else '❌ FALLIDA'}")
    
    print("\n=== PRUEBAS COMPLETADAS ===\n")
