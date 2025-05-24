"""
Script para crear datos de prueba realistas en la base de datos.
Esto resuelve el problema de UUIDs ficticios en los tests.
"""

import sys
import os
import uuid
from datetime import datetime, timedelta
import random

# Agregar el directorio raíz al path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
sys.path.insert(0, root_dir)

from App.DB.supabase_client import get_supabase_client

def create_test_users():
    """Crear usuarios de prueba."""
    supabase = get_supabase_client()
    
    test_users = [
        {
            "id": str(uuid.uuid4()),
            "full_name": "Juan Carlos Pérez",
            "email": "juan.perez@empresa.com",
            "phone": "+57 300 123 4567",
            "company": "TechCorp S.A.S",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "full_name": "María Elena González",
            "email": "maria.gonzalez@startup.co",
            "phone": "+57 301 987 6543",
            "company": "InnovaStartup",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "full_name": "Carlos Alberto Rodríguez",
            "email": "carlos.rodriguez@pyme.com",
            "phone": "+57 302 456 7890",
            "company": "PYME Digital",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "full_name": "Ana Sofía Martínez",
            "email": "ana.martinez@consultora.com",
            "phone": "+57 303 654 3210",
            "company": "Consultora Estratégica",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "full_name": "Roberto Silva",
            "email": "roberto.silva@tech.com",
            "phone": "+57 304 111 2222",
            "company": "TechSolutions",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    ]
    
    try:
        # Insertar usuarios
        response = supabase.table("users").insert(test_users).execute()
        print(f"✅ Creados {len(test_users)} usuarios de prueba")
        return [user["id"] for user in test_users]
    except Exception as e:
        print(f"❌ Error creando usuarios: {str(e)}")
        return []

def create_test_lead_qualifications(user_ids):
    """Crear lead qualifications de prueba."""
    supabase = get_supabase_client()
    
    qualification_steps = [
        "initial_contact", "needs_assessment", "proposal_sent", 
        "negotiation", "closing", "won", "lost"
    ]
    
    test_qualifications = []
    
    for i, user_id in enumerate(user_ids):
        qualification = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "current_step": random.choice(qualification_steps[:5]),  # No incluir won/lost
            "consent": random.choice([True, False]),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        test_qualifications.append(qualification)
    
    try:
        response = supabase.table("lead_qualification").insert(test_qualifications).execute()
        print(f"✅ Creadas {len(test_qualifications)} lead qualifications de prueba")
        return [qual["id"] for qual in test_qualifications]
    except Exception as e:
        print(f"❌ Error creando lead qualifications: {str(e)}")
        return []

def create_test_meetings(user_ids, qualification_ids):
    """Crear meetings de prueba."""
    supabase = get_supabase_client()
    
    meeting_subjects = [
        "Reunión inicial - Presentación de servicios",
        "Demo técnica - Plataforma de automatización",
        "Reunión de seguimiento - Propuesta comercial",
        "Sesión de Q&A - Dudas técnicas",
        "Reunión de cierre - Negociación final"
    ]
    
    test_meetings = []
    
    for i in range(min(len(user_ids), len(qualification_ids))):
        # Crear meetings en diferentes fechas
        start_time = datetime.now() + timedelta(days=random.randint(1, 30), hours=random.randint(9, 16))
        end_time = start_time + timedelta(hours=1)
        
        meeting = {
            "id": str(uuid.uuid4()),
            "user_id": user_ids[i],
            "lead_qualification_id": qualification_ids[i],
            "subject": random.choice(meeting_subjects),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "status": random.choice(["scheduled", "completed", "cancelled"]),
            "online_meeting_url": f"https://teams.microsoft.com/l/meetup-join/meeting_{random.randint(100000, 999999)}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        test_meetings.append(meeting)
    
    try:
        response = supabase.table("meetings").insert(test_meetings).execute()
        print(f"✅ Creadas {len(test_meetings)} meetings de prueba")
        return [meeting["id"] for meeting in test_meetings]
    except Exception as e:
        print(f"❌ Error creando meetings: {str(e)}")
        return []

def create_test_conversations(user_ids):
    """Crear conversaciones de prueba."""
    supabase = get_supabase_client()
    
    platforms = ["whatsapp", "web", "email", "phone"]
    
    test_conversations = []
    
    for i, user_id in enumerate(user_ids):
        conversation = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "platform": random.choice(platforms),
            "external_id": f"ext_{random.randint(100000, 999999)}_{i}",
            "status": random.choice(["active", "resolved", "pending"]),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        test_conversations.append(conversation)
    
    try:
        response = supabase.table("conversations").insert(test_conversations).execute()
        print(f"✅ Creadas {len(test_conversations)} conversaciones de prueba")
        return [conv["id"] for conv in test_conversations]
    except Exception as e:
        print(f"❌ Error creando conversaciones: {str(e)}")
        return []

def create_test_messages(conversation_ids, user_ids):
    """Crear mensajes de prueba."""
    supabase = get_supabase_client()
    
    message_contents = [
        "Hola, me interesa conocer más sobre sus servicios de automatización.",
        "¿Podrían agendar una demo para la próxima semana?",
        "Tengo algunas dudas sobre la integración con nuestros sistemas actuales.",
        "¿Cuál es el tiempo estimado de implementación?",
        "Necesito una cotización para un proyecto de 50 usuarios.",
        "¿Ofrecen soporte técnico 24/7?",
        "Me gustaría programar una reunión con el equipo técnico."
    ]
    
    test_messages = []
    
    for i, conversation_id in enumerate(conversation_ids):
        # Crear 2-4 mensajes por conversación
        num_messages = random.randint(2, 4)
        
        for j in range(num_messages):
            message = {
                "id": str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "role": "user" if j % 2 == 0 else "assistant",
                "content": random.choice(message_contents),
                "message_type": random.choice(["text", "file", "image"]),
                "created_at": (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat()
            }
            test_messages.append(message)
    
    try:
        response = supabase.table("messages").insert(test_messages).execute()
        print(f"✅ Creados {len(test_messages)} mensajes de prueba")
        return [msg["id"] for msg in test_messages]
    except Exception as e:
        print(f"❌ Error creando mensajes: {str(e)}")
        return []

def get_existing_test_ids():
    """Obtener IDs existentes para usar en tests."""
    supabase = get_supabase_client()
    
    try:
        # Obtener IDs existentes
        users = supabase.table("users").select("id").limit(5).execute()
        qualifications = supabase.table("lead_qualification").select("id").limit(5).execute()
        meetings = supabase.table("meetings").select("id").limit(5).execute()
        conversations = supabase.table("conversations").select("id").limit(5).execute()
        messages = supabase.table("messages").select("id").limit(5).execute()
        
        return {
            "user_ids": [u["id"] for u in users.data] if users.data else [],
            "qualification_ids": [q["id"] for q in qualifications.data] if qualifications.data else [],
            "meeting_ids": [m["id"] for m in meetings.data] if meetings.data else [],
            "conversation_ids": [c["id"] for c in conversations.data] if conversations.data else [],
            "message_ids": [m["id"] for m in messages.data] if messages.data else []
        }
    except Exception as e:
        print(f"❌ Error obteniendo IDs existentes: {str(e)}")
        return {}

def main():
    """Función principal para crear todos los datos de prueba."""
    print("🚀 Iniciando creación de datos de prueba...")
    
    # Crear usuarios
    user_ids = create_test_users()
    if not user_ids:
        print("❌ No se pudieron crear usuarios. Abortando.")
        return
    
    # Crear lead qualifications
    qualification_ids = create_test_lead_qualifications(user_ids)
    
    # Crear meetings
    meeting_ids = create_test_meetings(user_ids, qualification_ids)
    
    # Crear conversaciones
    conversation_ids = create_test_conversations(user_ids)
    
    # Crear mensajes
    message_ids = create_test_messages(conversation_ids, user_ids)
    
    print("\n📊 Resumen de datos creados:")
    print(f"   👥 Usuarios: {len(user_ids)}")
    print(f"   🎯 Lead Qualifications: {len(qualification_ids)}")
    print(f"   📅 Meetings: {len(meeting_ids)}")
    print(f"   💬 Conversaciones: {len(conversation_ids)}")
    print(f"   📝 Mensajes: {len(message_ids)}")
    
    # Mostrar IDs para usar en tests
    print("\n🔑 IDs para usar en tests:")
    if user_ids:
        print(f"   User ID ejemplo: {user_ids[0]}")
    if qualification_ids:
        print(f"   Qualification ID ejemplo: {qualification_ids[0]}")
    if meeting_ids:
        print(f"   Meeting ID ejemplo: {meeting_ids[0]}")
    if conversation_ids:
        print(f"   Conversation ID ejemplo: {conversation_ids[0]}")
    if message_ids:
        print(f"   Message ID ejemplo: {message_ids[0]}")
    
    print("\n✅ Datos de prueba creados exitosamente!")

if __name__ == "__main__":
    main()
