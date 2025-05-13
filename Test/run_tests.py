#!/usr/bin/env python3
# Test/run_tests.py

"""
Script para ejecutar todas las pruebas de conexión a Supabase y almacenamiento del agente.
Este script ejecuta ambas pruebas y muestra un resumen de los resultados.
"""

import os
import sys
import logging
import time
from dotenv import load_dotenv

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

def print_header(title):
    """Imprime un encabezado formateado"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def print_section(title):
    """Imprime un título de sección formateado"""
    print("\n" + "-" * 60)
    print(f" {title} ".center(60, "-"))
    print("-" * 60 + "\n")

def run_test(test_module_name, test_function_name):
    """Ejecuta una prueba específica y captura su resultado"""
    try:
        # Importar el módulo de prueba
        module = __import__(f"Test.{test_module_name}", fromlist=[test_function_name])
        
        # Obtener la función de prueba
        test_function = getattr(module, test_function_name)
        
        # Ejecutar la prueba
        start_time = time.time()
        result = test_function()
        elapsed_time = time.time() - start_time
        
        return {
            "success": result,
            "elapsed_time": elapsed_time
        }
    except Exception as e:
        logger.error(f"Error al ejecutar la prueba {test_module_name}.{test_function_name}: {str(e)}")
        import traceback
        logger.error(f"Traza completa: {traceback.format_exc()}")
        
        return {
            "success": False,
            "error": str(e),
            "elapsed_time": 0
        }

def main():
    """Función principal que ejecuta todas las pruebas"""
    print_header("PRUEBAS DE SUPABASE Y ALMACENAMIENTO DEL AGENTE")
    
    # Verificar variables de entorno
    print_section("Verificando variables de entorno")
    supabase_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    print(f"NEXT_PUBLIC_SUPABASE_URL: {'✅ Configurado' if supabase_url else '❌ No configurado'}")
    print(f"SUPABASE_SERVICE_ROLE_KEY: {'✅ Configurado' if supabase_key else '❌ No configurado'}")
    
    if not supabase_url or not supabase_key:
        print("\n⚠️ Advertencia: Las variables de entorno de Supabase no están configuradas.")
        print("Es posible que las pruebas fallen o utilicen el cliente mock.")
        print("Asegúrate de configurar las variables en el archivo .env:")
        print("  NEXT_PUBLIC_SUPABASE_URL=https://tu-proyecto.supabase.co")
        print("  SUPABASE_SERVICE_ROLE_KEY=tu-clave-de-servicio")
    
    # Ejecutar prueba de conexión a Supabase
    print_section("Ejecutando prueba de conexión a Supabase")
    connection_result = run_test("test_supabase_connection", "test_supabase_connection")
    
    if connection_result["success"]:
        print("✅ Conexión a Supabase: EXITOSA")
        
        # Ejecutar prueba de operaciones CRUD
        print_section("Ejecutando prueba de operaciones CRUD")
        crud_result = run_test("test_supabase_connection", "test_crud_operations")
        
        if crud_result["success"]:
            print("✅ Operaciones CRUD: EXITOSAS")
        else:
            print("❌ Operaciones CRUD: FALLIDAS")
            if "error" in crud_result:
                print(f"Error: {crud_result['error']}")
    else:
        print("❌ Conexión a Supabase: FALLIDA")
        if "error" in connection_result:
            print(f"Error: {connection_result['error']}")
        
        print("\n⚠️ No se ejecutarán las pruebas de operaciones CRUD ni de almacenamiento del agente")
        print("debido a que la conexión a Supabase falló.")
        return
    
    # Ejecutar prueba de almacenamiento del agente
    print_section("Ejecutando prueba de almacenamiento del agente")
    print("Esta prueba puede tardar varios minutos...")
    
    # Importar y ejecutar directamente para ver la salida en tiempo real
    try:
        from Test.test_agent_storage import test_agent_storage
        test_agent_storage()
        agent_storage_success = True
    except Exception as e:
        print(f"❌ Error al ejecutar la prueba de almacenamiento del agente: {str(e)}")
        import traceback
        print(f"Traza completa: {traceback.format_exc()}")
        agent_storage_success = False
    
    # Mostrar resumen de resultados
    print_section("RESUMEN DE RESULTADOS")
    
    print(f"Conexión a Supabase: {'✅ EXITOSA' if connection_result['success'] else '❌ FALLIDA'}")
    print(f"Operaciones CRUD: {'✅ EXITOSAS' if crud_result.get('success', False) else '❌ FALLIDAS'}")
    print(f"Almacenamiento del agente: {'✅ EXITOSO' if agent_storage_success else '❌ FALLIDO'}")
    
    # Conclusión
    print_section("CONCLUSIÓN")
    
    if connection_result["success"] and crud_result.get("success", False) and agent_storage_success:
        print("✅ Todas las pruebas han sido exitosas.")
        print("La conexión a Supabase funciona correctamente y el agente está guardando la información en la base de datos.")
    elif connection_result["success"] and crud_result.get("success", False) and not agent_storage_success:
        print("⚠️ La conexión a Supabase funciona correctamente, pero el agente no está guardando la información.")
        print("Posibles causas:")
        print("1. El agente no está configurado correctamente para usar Supabase.")
        print("2. Las funciones del agente no están llamando a las funciones de db_operations.py.")
        print("3. Hay errores en las funciones de db_operations.py que impiden guardar la información.")
    elif connection_result["success"] and not crud_result.get("success", False):
        print("⚠️ La conexión a Supabase funciona, pero las operaciones CRUD fallan.")
        print("Posibles causas:")
        print("1. Las políticas de seguridad de Supabase no permiten las operaciones CRUD.")
        print("2. La estructura de las tablas en Supabase no coincide con la esperada.")
        print("3. La clave de servicio no tiene los permisos necesarios.")
    else:
        print("❌ La conexión a Supabase no funciona.")
        print("Posibles causas:")
        print("1. Las variables de entorno no están configuradas correctamente.")
        print("2. El proyecto de Supabase no existe o no está accesible.")
        print("3. La clave de servicio no es válida.")
    
    print("\nPara resolver estos problemas, revisa la documentación de Supabase y asegúrate de que:")
    print("1. Las variables de entorno están configuradas correctamente en el archivo .env.")
    print("2. El proyecto de Supabase existe y está accesible.")
    print("3. La clave de servicio tiene los permisos necesarios.")
    print("4. Las políticas de seguridad de Supabase permiten las operaciones necesarias.")
    print("5. La estructura de las tablas en Supabase coincide con la esperada.")
    
    print_header("FIN DE LAS PRUEBAS")

if __name__ == "__main__":
    main()
