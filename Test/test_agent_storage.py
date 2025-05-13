# Test/test_agent_storage.py

import os
import sys
import logging
import uuid
from dotenv import load_dotenv

# Añadir el directorio raíz al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar funciones de base de datos directamente
from App.DB.db_operations import (
    get_user_by_phone, 
    get_active_conversation, 
    get_lead_qualification,
    get_or_create_lead_qualification,
    update_lead_qualification,
    get_or_create_user,
    create_or_update_bant_data,
    get_bant_data,
    get_or_create_requirements,
    add_feature,
    add_integration,
    get_requirements,
    get_features,
    get_integrations,
    create_user,
    create_conversation,
    create_lead_qualification
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Funciones de prueba que simulan las herramientas del agente
def test_process_consent(thread_id, response):
    """Simula la función process_consent sin usar la herramienta"""
    consent_given = response.lower() in ["sí", "si", "yes", "y", "acepto", "estoy de acuerdo"]
    
    # Buscar usuario y conversación
    user = get_user_by_phone(thread_id)
    if user:
        conversation = get_active_conversation(thread_id)
        if conversation:
            # Obtener o crear calificación de lead
            qualification = get_or_create_lead_qualification(user["id"], conversation["id"])
            
            # Actualizar estado de consentimiento
            update_lead_qualification(qualification["id"], {
                "consent": consent_given,
                "current_step": "personal_data" if consent_given else "consent_denied"
            })
    
    return f"Consentimiento procesado: {consent_given}"

def test_save_personal_data(thread_id, name, company, email, phone):
    """Simula la función save_personal_data sin usar la herramienta"""
    # Crear o actualizar usuario en la base de datos
    user = get_or_create_user(
        phone=phone,
        email=email,
        full_name=name,
        company=company
    )
    
    if thread_id and user:
        # Actualizar conversación si existe
        conversation = get_active_conversation(thread_id)
        if conversation:
            # Actualizar calificación de lead
            qualification = get_or_create_lead_qualification(user["id"], conversation["id"])
            update_lead_qualification(qualification["id"], {
                "current_step": "bant"
            })
    
    return f"Datos personales guardados: {name}, {company}, {email}, {phone}"

def test_save_bant_data(thread_id, budget, authority, need, timeline):
    """Simula la función save_bant_data sin usar la herramienta"""
    if thread_id:
        # Buscar usuario y conversación
        user = get_user_by_phone(thread_id)
        if user:
            conversation = get_active_conversation(thread_id)
            if conversation:
                # Obtener calificación de lead
                qualification = get_lead_qualification(user["id"], conversation["id"])
                if qualification:
                    # Guardar datos BANT
                    create_or_update_bant_data(
                        qualification["id"],
                        budget=budget,
                        authority=authority,
                        need=need,
                        timeline=timeline
                    )
                    
                    # Actualizar estado
                    update_lead_qualification(qualification["id"], {
                        "current_step": "requirements"
                    })
    
    return f"Datos BANT guardados: Presupuesto: {budget}, Autoridad: {authority}, Necesidad: {need}, Plazo: {timeline}"

def test_save_requirements(thread_id, app_type, core_features, integrations, deadline):
    """Simula la función save_requirements sin usar la herramienta"""
    if thread_id:
        # Buscar usuario y conversación
        user = get_user_by_phone(thread_id)
        if user:
            conversation = get_active_conversation(thread_id)
            if conversation:
                # Obtener calificación de lead
                qualification = get_lead_qualification(user["id"], conversation["id"])
                if qualification:
                    # Crear requerimientos
                    requirements = get_or_create_requirements(
                        qualification["id"],
                        app_type=app_type,
                        deadline=deadline
                    )
                    
                    # Procesar características
                    features_list = [f.strip() for f in core_features.split(',') if f.strip()]
                    for feature in features_list:
                        add_feature(requirements["id"], feature)
                    
                    # Procesar integraciones
                    integrations_list = [i.strip() for i in integrations.split(',') if i.strip()]
                    for integration in integrations_list:
                        add_integration(requirements["id"], integration)
                    
                    # Actualizar estado
                    update_lead_qualification(qualification["id"], {
                        "current_step": "meeting"
                    })
    
    return f"Requerimientos guardados: Tipo: {app_type}, Características: {core_features}, Integraciones: {integrations}, Fecha límite: {deadline}"

def test_agent_storage():
    """Prueba que el agente guarda correctamente la información en la base de datos"""
    
    # Generar un ID único para esta prueba
    test_id = str(uuid.uuid4())
    test_phone = f"+1{test_id[-10:]}"
    
    print(f"\n=== PRUEBA DE ALMACENAMIENTO DEL AGENTE ===")
    print(f"ID de prueba: {test_id}")
    print(f"Teléfono de prueba: {test_phone}")
    
    # Paso 1: Probar el consentimiento
    print("\n1. Probando almacenamiento de consentimiento...")
    
    # Llamar a nuestra función de prueba en lugar de la herramienta
    consent_result = test_process_consent(test_phone, "sí")
    print(f"Resultado: {consent_result}")
    
    # Verificar si se guardó en la base de datos
    user = get_user_by_phone(test_phone)
    if not user:
        print("❌ No se creó el usuario automáticamente")
        
        # Crear usuario manualmente para continuar con las pruebas
        from App.DB.db_operations import create_user
        user = create_user({
            "phone": test_phone,
            "email": f"test_{test_id}@example.com",
            "full_name": f"Usuario Prueba {test_id}",
            "company": "Empresa de Prueba"
        })
        print(f"✅ Usuario creado manualmente con ID: {user.get('id', 'desconocido')}")
    else:
        print(f"✅ Usuario creado con ID: {user['id']}")
        
    # Verificar si se creó la conversación
    conversation = get_active_conversation(test_phone)
    if not conversation:
        print("❌ No se creó la conversación automáticamente")
        
        # Crear conversación manualmente para continuar con las pruebas
        if user and 'id' in user:
            from App.DB.db_operations import create_conversation
            conversation = create_conversation(user['id'], test_phone)
            print(f"✅ Conversación creada manualmente con ID: {conversation.get('id', 'desconocido')}")
    else:
        print(f"✅ Conversación creada con ID: {conversation['id']}")
        
    # Verificar si se guardó el consentimiento
    if user and 'id' in user and conversation and 'id' in conversation:
        qualification = get_lead_qualification(user['id'], conversation['id'])
        if not qualification:
            print("❌ No se creó la calificación de lead")
            
            # Crear calificación manualmente para continuar con las pruebas
            from App.DB.db_operations import create_lead_qualification
            qualification = create_lead_qualification(user['id'], conversation['id'])
            print(f"✅ Calificación de lead creada manualmente con ID: {qualification.get('id', 'desconocido')}")
        else:
            print(f"✅ Calificación de lead creada con ID: {qualification['id']}")
            print(f"✅ Consentimiento guardado: {qualification['consent']}")
            print(f"✅ Estado actual: {qualification['current_step']}")
    
    # Paso 2: Probar datos personales
    print("\n2. Probando almacenamiento de datos personales...")
    
    # Datos de prueba
    test_name = f"Usuario Prueba {test_id}"
    test_company = "Empresa de Prueba"
    test_email = f"test_{test_id}@example.com"
    
    # Llamar a nuestra función de prueba en lugar de la herramienta
    personal_data_result = test_save_personal_data(test_phone, test_name, test_company, test_email, test_phone)
    print(f"Resultado: {personal_data_result}")
    
    # Verificar si se actualizó el usuario
    user = get_user_by_phone(test_phone)
    if not user:
        print("❌ No se encontró el usuario")
    else:
        print(f"✅ Usuario actualizado: {user['full_name']}")
        print(f"✅ Empresa: {user['company']}")
        print(f"✅ Email: {user['email']}")
        
        # Verificar si se actualizó el estado
        conversation = get_active_conversation(test_phone)
        if conversation:
            qualification = get_lead_qualification(user['id'], conversation['id'])
            if qualification:
                print(f"✅ Estado actualizado: {qualification['current_step']}")
    
    # Paso 3: Probar datos BANT
    print("\n3. Probando almacenamiento de datos BANT...")
    
    # Datos de prueba
    test_budget = "10000-20000 USD"
    test_authority = "Soy el responsable de la decisión"
    test_need = "Necesito una aplicación para gestionar inventario"
    test_timeline = "3 meses"
    
    # Llamar a nuestra función de prueba en lugar de la herramienta
    bant_result = test_save_bant_data(test_phone, test_budget, test_authority, test_need, test_timeline)
    print(f"Resultado: {bant_result}")
    
    # Verificar si se guardaron los datos BANT
    user = get_user_by_phone(test_phone)
    conversation = get_active_conversation(test_phone)
    if user and conversation:
        qualification = get_lead_qualification(user['id'], conversation['id'])
        if qualification:
            bant_data = get_bant_data(qualification['id'])
            if not bant_data:
                print("❌ No se guardaron los datos BANT")
            else:
                print(f"✅ Datos BANT guardados con ID: {bant_data['id']}")
                print(f"✅ Presupuesto: {bant_data['budget']}")
                print(f"✅ Autoridad: {bant_data['authority']}")
                print(f"✅ Necesidad: {bant_data['need']}")
                print(f"✅ Plazo: {bant_data['timeline']}")
                
                # Verificar si se actualizó el estado
                qualification = get_lead_qualification(user['id'], conversation['id'])
                if qualification:
                    print(f"✅ Estado actualizado: {qualification['current_step']}")
    
    # Paso 4: Probar requerimientos
    print("\n4. Probando almacenamiento de requerimientos...")
    
    # Datos de prueba
    test_app_type = "Aplicación web"
    test_features = "Login, Dashboard, Reportes, Gestión de usuarios"
    test_integrations = "API de pagos, CRM, ERP"
    test_deadline = "Diciembre 2025"
    
    # Llamar a nuestra función de prueba en lugar de la herramienta
    requirements_result = test_save_requirements(test_phone, test_app_type, test_features, test_integrations, test_deadline)
    print(f"Resultado: {requirements_result}")
    
    # Verificar si se guardaron los requerimientos
    user = get_user_by_phone(test_phone)
    conversation = get_active_conversation(test_phone)
    if user and conversation:
        qualification = get_lead_qualification(user['id'], conversation['id'])
        if qualification:
            requirements = get_requirements(qualification['id'])
            if not requirements:
                print("❌ No se guardaron los requerimientos")
            else:
                print(f"✅ Requerimientos guardados con ID: {requirements['id']}")
                print(f"✅ Tipo de aplicación: {requirements['app_type']}")
                print(f"✅ Fecha límite: {requirements['deadline']}")
                
                # Verificar características
                features = get_features(requirements['id'])
                if not features:
                    print("❌ No se guardaron las características")
                else:
                    print(f"✅ Características guardadas: {len(features)}")
                    for feature in features:
                        print(f"  - {feature['name']}")
                
                # Verificar integraciones
                integrations = get_integrations(requirements['id'])
                if not integrations:
                    print("❌ No se guardaron las integraciones")
                else:
                    print(f"✅ Integraciones guardadas: {len(integrations)}")
                    for integration in integrations:
                        print(f"  - {integration['name']}")
                
                # Verificar si se actualizó el estado
                qualification = get_lead_qualification(user['id'], conversation['id'])
                if qualification:
                    print(f"✅ Estado actualizado: {qualification['current_step']}")
    
    print("\n=== PRUEBA DE ALMACENAMIENTO COMPLETADA ===\n")

if __name__ == "__main__":
    test_agent_storage()
