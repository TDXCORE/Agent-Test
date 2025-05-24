"""
Operaciones de base de datos para interactuar con Supabase.
Este archivo proporciona funciones para realizar operaciones CRUD en la base de datos.
"""

from App.DB.supabase_client import get_supabase_client
from typing import Dict, List, Optional, Any, Union
import uuid

# Obtener cliente de Supabase
supabase = get_supabase_client()

# ----- OPERACIONES DE USUARIOS -----

def get_all_users_from_db() -> List[Dict]:
    """
    Obtiene todos los usuarios de la base de datos.
    
    Returns:
        Lista de usuarios
    """
    response = supabase.table("users").select(
        "id, full_name, phone, email, company, created_at"
    ).execute()
    
    return response.data if response.data else []

def get_user_by_phone(phone: str) -> Optional[Dict]:
    """
    Obtiene un usuario por su número de teléfono.
    
    Args:
        phone: Número de teléfono del usuario
        
    Returns:
        Datos del usuario o None si no existe
    """
    response = supabase.table("users").select("*").eq("phone", phone).execute()
    return response.data[0] if response.data else None

def get_user_by_email(email: str) -> Optional[Dict]:
    """
    Obtiene un usuario por su correo electrónico.
    
    Args:
        email: Correo electrónico del usuario
        
    Returns:
        Datos del usuario o None si no existe
    """
    response = supabase.table("users").select("*").eq("email", email).execute()
    return response.data[0] if response.data else None

def get_user_by_id(user_id: str) -> Optional[Dict]:
    """
    Obtiene un usuario por su ID.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        Datos del usuario o None si no existe
    """
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    return response.data[0] if response.data else None

def create_user(user_data: Dict) -> Dict:
    """
    Crea un nuevo usuario.
    
    Args:
        user_data: Datos del usuario (full_name, email, phone, company)
        
    Returns:
        Datos del usuario creado
    """
    response = supabase.table("users").insert(user_data).execute()
    return response.data[0] if response.data else {}

def update_user(user_id: str, user_data: Dict) -> Dict:
    """
    Actualiza los datos de un usuario.
    
    Args:
        user_id: ID del usuario
        user_data: Datos a actualizar
        
    Returns:
        Datos del usuario actualizado
    """
    # Asegurar que updated_at se actualice
    if "updated_at" not in user_data:
        user_data["updated_at"] = "now()"
        
    response = supabase.table("users").update(user_data).eq("id", user_id).execute()
    return response.data[0] if response.data else {}

def get_or_create_user(phone: str, email: Optional[str] = None, full_name: Optional[str] = None, company: Optional[str] = None) -> Dict:
    """
    Obtiene un usuario existente o crea uno nuevo si no existe.
    
    Args:
        phone: Número de teléfono del usuario
        email: Correo electrónico (opcional)
        full_name: Nombre completo (opcional)
        company: Empresa (opcional)
        
    Returns:
        Datos del usuario
    """
    # Buscar por teléfono
    user = get_user_by_phone(phone)
    
    # Si no existe y tenemos email, buscar por email
    if not user and email:
        user = get_user_by_email(email)
    
    # Si no existe, crear nuevo usuario
    if not user:
        user_data = {
            "phone": phone,
            "email": email,
            "full_name": full_name or f"Usuario {phone}",
            "company": company
        }
        user = create_user(user_data)
    
    return user

def delete_user(user_id: str) -> bool:
    """
    Elimina un usuario o lo marca como inactivo.
    
    En lugar de eliminar físicamente el usuario, lo marcamos como inactivo
    para mantener la integridad referencial.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        True si se actualizó correctamente, False en caso contrario
    """
    # Marcar como inactivo en lugar de eliminar físicamente
    update_data = {
        "active": False,
        "updated_at": "now()"
    }
    
    response = supabase.table("users").update(update_data).eq("id", user_id).execute()
    return len(response.data) > 0 if response.data else False

# ----- OPERACIONES DE CONVERSACIONES -----

def get_active_conversation(external_id: str, platform: str = "whatsapp") -> Optional[Dict]:
    """
    Obtiene una conversación activa por su ID externo y plataforma.
    
    Args:
        external_id: ID externo (número de teléfono para WhatsApp)
        platform: Plataforma (whatsapp, web, etc.)
        
    Returns:
        Datos de la conversación o None si no existe
    """
    response = supabase.table("conversations") \
        .select("*") \
        .eq("external_id", external_id) \
        .eq("platform", platform) \
        .eq("status", "active") \
        .execute()
    
    return response.data[0] if response.data else None

def create_conversation(user_id: str, external_id: str, platform: str = "whatsapp") -> Dict:
    """
    Crea una nueva conversación.
    
    Args:
        user_id: ID del usuario
        external_id: ID externo (número de teléfono para WhatsApp)
        platform: Plataforma (whatsapp, web, etc.)
        
    Returns:
        Datos de la conversación creada
    """
    conversation_data = {
        "user_id": user_id,
        "external_id": external_id,
        "platform": platform,
        "status": "active"
    }
    
    response = supabase.table("conversations").insert(conversation_data).execute()
    return response.data[0] if response.data else {}

def close_conversation(conversation_id: str) -> Dict:
    """
    Cierra una conversación.
    
    Args:
        conversation_id: ID de la conversación
        
    Returns:
        Datos de la conversación actualizada
    """
    update_data = {
        "status": "closed",
        "updated_at": "now()"
    }
    
    response = supabase.table("conversations").update(update_data).eq("id", conversation_id).execute()
    return response.data[0] if response.data else {}

def get_or_create_conversation(user_id: str, external_id: str, platform: str = "whatsapp") -> Dict:
    """
    Obtiene una conversación activa o crea una nueva si no existe.
    
    Args:
        user_id: ID del usuario
        external_id: ID externo (número de teléfono para WhatsApp)
        platform: Plataforma (whatsapp, web, etc.)
        
    Returns:
        Datos de la conversación
    """
    conversation = get_active_conversation(external_id, platform)
    
    if not conversation:
        conversation = create_conversation(user_id, external_id, platform)
    
    return conversation

def get_conversation_by_id(conversation_id: str) -> Optional[Dict]:
    """
    Obtiene una conversación por su ID.
    
    Args:
        conversation_id: ID de la conversación
        
    Returns:
        Datos de la conversación o None si no existe
    """
    response = supabase.table("conversations").select("*").eq("id", conversation_id).execute()
    return response.data[0] if response.data else None

def get_user_conversations(user_id: str, include_closed: bool = False) -> List[Dict]:
    """
    Obtiene todas las conversaciones de un usuario.
    
    Args:
        user_id: ID del usuario
        include_closed: Si es True, incluye conversaciones cerradas
        
    Returns:
        Lista de conversaciones
    """
    query = supabase.table("conversations").select("*").eq("user_id", user_id)
    
    if not include_closed:
        query = query.eq("status", "active")
    
    response = query.order("created_at", desc=True).execute()
    return response.data if response.data else []

# ----- OPERACIONES DE MENSAJES -----

def get_conversation_messages(conversation_id: str) -> List[Dict]:
    """
    Obtiene todos los mensajes de una conversación.
    
    Args:
        conversation_id: ID de la conversación
        
    Returns:
        Lista de mensajes
    """
    response = supabase.table("messages") \
        .select("*") \
        .eq("conversation_id", conversation_id) \
        .order("created_at") \
        .execute()
    
    return response.data

def add_message(conversation_id: str, role: str, content: str, message_type: str = "text", 
                media_url: Optional[str] = None, external_id: Optional[str] = None, read: bool = False) -> Dict:
    """
    Añade un mensaje a una conversación.
    
    Args:
        conversation_id: ID de la conversación
        role: Rol del mensaje (user, assistant, system)
        content: Contenido del mensaje
        message_type: Tipo de mensaje (text, image, audio, video)
        media_url: URL del archivo multimedia (opcional)
        external_id: ID externo del mensaje (opcional)
        read: Indica si el mensaje ha sido leído (por defecto False)
        
    Returns:
        Datos del mensaje creado
    """
    message_data = {
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "message_type": message_type,
        "media_url": media_url,
        "external_id": external_id,
        "read": read
    }
    
    response = supabase.table("messages").insert(message_data).execute()
    return response.data[0] if response.data else {}

def get_conversation_history(conversation_id: str, max_messages: int = 10) -> List[Dict]:
    """
    Obtiene el historial de mensajes de una conversación en formato para el agente,
    limitando la cantidad de mensajes para reducir el consumo de tokens.
    
    Args:
        conversation_id: ID de la conversación
        max_messages: Número máximo de mensajes a recuperar (por defecto 10)
        
    Returns:
        Lista de mensajes en formato {role, content}
    """
    # Obtener todos los mensajes de la conversación
    all_messages = get_conversation_messages(conversation_id)
    
    # Limitar la cantidad de mensajes, pero asegurar que tengamos el mensaje de sistema
    system_messages = [msg for msg in all_messages if msg["role"] == "system"]
    non_system_messages = [msg for msg in all_messages if msg["role"] != "system"]
    
    # Tomar los mensajes más recientes, pero respetando el límite
    recent_messages = non_system_messages[-max_messages:] if len(non_system_messages) > max_messages else non_system_messages
    
    # Combinar mensajes de sistema con los mensajes recientes
    messages = system_messages + recent_messages
    
    # Convertir al formato que espera el agente
    history = []
    
    # Asegurar que siempre haya un mensaje de sistema al inicio
    system_message_exists = False
    
    for msg in messages:
        # Verificar si ya existe un mensaje de sistema
        if msg["role"] == "system":
            system_message_exists = True
        
        # Añadir el mensaje al historial
        history.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Si no hay mensaje de sistema, añadir uno al inicio
    if not system_message_exists and history:
        history.insert(0, {
            "role": "system",
            "content": "Iniciando conversación con un potencial cliente."
        })
    
    # Imprimir el historial para depuración
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Historial de conversación recuperado: {len(history)} mensajes (limitado a {max_messages} mensajes no-sistema)")
    for i, msg in enumerate(history):
        logger.info(f"Mensaje {i+1}: {msg['role']} - {msg['content'][:50]}...")
    
    return history

# ----- OPERACIONES DE CALIFICACIÓN DE LEADS -----

def get_lead_qualification(user_id: str, conversation_id: str) -> Optional[Dict]:
    """
    Obtiene la calificación de lead para un usuario y conversación.
    
    Args:
        user_id: ID del usuario
        conversation_id: ID de la conversación
        
    Returns:
        Datos de la calificación o None si no existe
    """
    response = supabase.table("lead_qualification") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("conversation_id", conversation_id) \
        .execute()
    
    return response.data[0] if response.data else None

def create_lead_qualification(user_id: str, conversation_id: str) -> Dict:
    """
    Crea una nueva calificación de lead.
    
    Args:
        user_id: ID del usuario
        conversation_id: ID de la conversación
        
    Returns:
        Datos de la calificación creada
    """
    qualification_data = {
        "user_id": user_id,
        "conversation_id": conversation_id,
        "consent": False,
        "current_step": "start"
    }
    
    response = supabase.table("lead_qualification").insert(qualification_data).execute()
    return response.data[0] if response.data else {}

def update_lead_qualification(qualification_id: str, data: Dict) -> Dict:
    """
    Actualiza los datos de una calificación de lead.
    
    Args:
        qualification_id: ID de la calificación
        data: Datos a actualizar
        
    Returns:
        Datos de la calificación actualizada
    """
    # Asegurar que updated_at se actualice
    if "updated_at" not in data:
        data["updated_at"] = "now()"
        
    response = supabase.table("lead_qualification").update(data).eq("id", qualification_id).execute()
    return response.data[0] if response.data else {}

def get_or_create_lead_qualification(user_id: str, conversation_id: str) -> Dict:
    """
    Obtiene una calificación de lead existente o crea una nueva si no existe.
    
    Args:
        user_id: ID del usuario
        conversation_id: ID de la conversación
        
    Returns:
        Datos de la calificación
    """
    qualification = get_lead_qualification(user_id, conversation_id)
    
    if not qualification:
        qualification = create_lead_qualification(user_id, conversation_id)
    
    return qualification

# ----- OPERACIONES DE DATOS BANT -----

def get_bant_data(lead_qualification_id: str) -> Optional[Dict]:
    """
    Obtiene los datos BANT para una calificación de lead.
    
    Args:
        lead_qualification_id: ID de la calificación de lead
        
    Returns:
        Datos BANT o None si no existen
    """
    response = supabase.table("bant_data") \
        .select("*") \
        .eq("lead_qualification_id", lead_qualification_id) \
        .execute()
    
    return response.data[0] if response.data else None

def create_or_update_bant_data(lead_qualification_id: str, budget: str, authority: str, need: str, timeline: str) -> Dict:
    """
    Crea o actualiza los datos BANT para una calificación de lead.
    
    Args:
        lead_qualification_id: ID de la calificación de lead
        budget: Presupuesto
        authority: Nivel de autoridad
        need: Necesidad
        timeline: Plazo
        
    Returns:
        Datos BANT creados o actualizados
    """
    # Verificar si ya existen datos BANT
    bant_data = get_bant_data(lead_qualification_id)
    
    data = {
        "budget": budget,
        "authority": authority,
        "need": need,
        "timeline": timeline,
        "updated_at": "now()"
    }
    
    if bant_data:
        # Actualizar datos existentes
        response = supabase.table("bant_data").update(data).eq("id", bant_data["id"]).execute()
    else:
        # Crear nuevos datos
        data["lead_qualification_id"] = lead_qualification_id
        response = supabase.table("bant_data").insert(data).execute()
    
    return response.data[0] if response.data else {}

# ----- OPERACIONES DE REQUERIMIENTOS -----

def get_requirements(lead_qualification_id: str) -> Optional[Dict]:
    """
    Obtiene los requerimientos para una calificación de lead.
    
    Args:
        lead_qualification_id: ID de la calificación de lead
        
    Returns:
        Datos de requerimientos o None si no existen
    """
    response = supabase.table("requirements") \
        .select("*") \
        .eq("lead_qualification_id", lead_qualification_id) \
        .execute()
    
    return response.data[0] if response.data else None

def create_requirements(lead_qualification_id: str, app_type: str, deadline: str) -> Dict:
    """
    Crea nuevos requerimientos para una calificación de lead.
    
    Args:
        lead_qualification_id: ID de la calificación de lead
        app_type: Tipo de aplicación
        deadline: Fecha límite
        
    Returns:
        Datos de requerimientos creados
    """
    requirements_data = {
        "lead_qualification_id": lead_qualification_id,
        "app_type": app_type,
        "deadline": deadline
    }
    
    response = supabase.table("requirements").insert(requirements_data).execute()
    return response.data[0] if response.data else {}

def update_requirements(requirements_id: str, data: Dict) -> Dict:
    """
    Actualiza los requerimientos.
    
    Args:
        requirements_id: ID de los requerimientos
        data: Datos a actualizar
        
    Returns:
        Datos de requerimientos actualizados
    """
    # Asegurar que updated_at se actualice
    if "updated_at" not in data:
        data["updated_at"] = "now()"
        
    response = supabase.table("requirements").update(data).eq("id", requirements_id).execute()
    return response.data[0] if response.data else {}

def get_or_create_requirements(lead_qualification_id: str, app_type: str, deadline: str) -> Dict:
    """
    Obtiene requerimientos existentes o crea nuevos si no existen.
    
    Args:
        lead_qualification_id: ID de la calificación de lead
        app_type: Tipo de aplicación
        deadline: Fecha límite
        
    Returns:
        Datos de requerimientos
    """
    requirements = get_requirements(lead_qualification_id)
    
    if not requirements:
        requirements = create_requirements(lead_qualification_id, app_type, deadline)
    
    return requirements

# ----- OPERACIONES DE CARACTERÍSTICAS -----

def add_feature(requirement_id: str, name: str, description: Optional[str] = None) -> Dict:
    """
    Añade una característica a los requerimientos.
    
    Args:
        requirement_id: ID de los requerimientos
        name: Nombre de la característica
        description: Descripción (opcional)
        
    Returns:
        Datos de la característica creada
    """
    feature_data = {
        "requirement_id": requirement_id,
        "name": name,
        "description": description
    }
    
    response = supabase.table("features").insert(feature_data).execute()
    return response.data[0] if response.data else {}

def get_features(requirement_id: str) -> List[Dict]:
    """
    Obtiene todas las características de unos requerimientos.
    
    Args:
        requirement_id: ID de los requerimientos
        
    Returns:
        Lista de características
    """
    response = supabase.table("features") \
        .select("*") \
        .eq("requirement_id", requirement_id) \
        .execute()
    
    return response.data

# ----- OPERACIONES DE INTEGRACIONES -----

def add_integration(requirement_id: str, name: str, description: Optional[str] = None) -> Dict:
    """
    Añade una integración a los requerimientos.
    
    Args:
        requirement_id: ID de los requerimientos
        name: Nombre de la integración
        description: Descripción (opcional)
        
    Returns:
        Datos de la integración creada
    """
    integration_data = {
        "requirement_id": requirement_id,
        "name": name,
        "description": description
    }
    
    response = supabase.table("integrations").insert(integration_data).execute()
    return response.data[0] if response.data else {}

def get_integrations(requirement_id: str) -> List[Dict]:
    """
    Obtiene todas las integraciones de unos requerimientos.
    
    Args:
        requirement_id: ID de los requerimientos
        
    Returns:
        Lista de integraciones
    """
    response = supabase.table("integrations") \
        .select("*") \
        .eq("requirement_id", requirement_id) \
        .execute()
    
    return response.data

# ----- OPERACIONES DE REUNIONES -----

def create_meeting(user_id: str, lead_qualification_id: str, outlook_meeting_id: str, 
                  subject: str, start_time: str, end_time: str, 
                  online_meeting_url: Optional[str] = None) -> Dict:
    """
    Crea una nueva reunión.
    
    Args:
        user_id: ID del usuario
        lead_qualification_id: ID de la calificación de lead
        outlook_meeting_id: ID de la reunión en Outlook
        subject: Asunto
        start_time: Fecha y hora de inicio
        end_time: Fecha y hora de fin
        online_meeting_url: URL de la reunión online (opcional)
        
    Returns:
        Datos de la reunión creada
    """
    # Añadir logs detallados
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Creando reunión: user_id={user_id}, lead_qualification_id={lead_qualification_id}")
    
    meeting_data = {
        "user_id": user_id,
        "lead_qualification_id": lead_qualification_id,
        "outlook_meeting_id": outlook_meeting_id,
        "subject": subject,
        "start_time": start_time,
        "end_time": end_time,
        "status": "scheduled",
        "online_meeting_url": online_meeting_url
    }
    
    try:
        response = supabase.table("meetings").insert(meeting_data).execute()
        logger.info(f"Reunión creada exitosamente: {response.data[0] if response.data else None}")
        return response.data[0] if response.data else {}
    except Exception as e:
        logger.error(f"Error al crear reunión: {str(e)}")
        import traceback
        logger.error(f"Traza completa: {traceback.format_exc()}")
        return {}

def update_meeting_status(meeting_id: str, status: str) -> Dict:
    """
    Actualiza el estado de una reunión.
    
    Args:
        meeting_id: ID de la reunión
        status: Nuevo estado (scheduled, completed, cancelled, rescheduled)
        
    Returns:
        Datos de la reunión actualizada
    """
    update_data = {
        "status": status,
        "updated_at": "now()"
    }
    
    response = supabase.table("meetings").update(update_data).eq("id", meeting_id).execute()
    return response.data[0] if response.data else {}

def get_user_meetings(user_id: str) -> List[Dict]:
    """
    Obtiene todas las reuniones de un usuario.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        Lista de reuniones
    """
    response = supabase.table("meetings") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("start_time") \
        .execute()
    
    return response.data

def get_meeting_by_outlook_id(outlook_meeting_id: str) -> Optional[Dict]:
    """
    Obtiene una reunión por su ID de Outlook.
    
    Args:
        outlook_meeting_id: ID de la reunión en Outlook
        
    Returns:
        Datos de la reunión o None si no existe
    """
    response = supabase.table("meetings") \
        .select("*") \
        .eq("outlook_meeting_id", outlook_meeting_id) \
        .execute()
    
    return response.data[0] if response.data else None

# ----- OPERACIONES DE MENSAJES NO LEÍDOS -----

def mark_messages_as_read(conversation_id: str) -> int:
    """
    Marca todos los mensajes no leídos de una conversación como leídos.
    
    Args:
        conversation_id: ID de la conversación
        
    Returns:
        Número de mensajes actualizados
    """
    response = supabase.table("messages").update(
        {"read": True}
    ).eq("conversation_id", conversation_id).eq("read", False).execute()
    
    return len(response.data) if response.data else 0

def update_message(message_id: str, data: Dict) -> Dict:
    """
    Actualiza un mensaje existente.
    
    Args:
        message_id: ID del mensaje
        data: Datos a actualizar
        
    Returns:
        Datos del mensaje actualizado
    """
    # Asegurar que updated_at se actualice
    if "updated_at" not in data:
        data["updated_at"] = "now()"
        
    response = supabase.table("messages").update(data).eq("id", message_id).execute()
    return response.data[0] if response.data else {}

def delete_message(message_id: str) -> bool:
    """
    Elimina un mensaje.
    
    Args:
        message_id: ID del mensaje
        
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    response = supabase.table("messages").delete().eq("id", message_id).execute()
    return len(response.data) > 0 if response.data else False

def get_message_by_id(message_id: str) -> Optional[Dict]:
    """
    Obtiene un mensaje por su ID.
    
    Args:
        message_id: ID del mensaje
        
    Returns:
        Datos del mensaje o None si no existe
    """
    response = supabase.table("messages").select("*").eq("id", message_id).execute()
    return response.data[0] if response.data else None

# ----- OPERACIONES DE ESTADO DEL AGENTE -----

def update_agent_status(conversation_id: str, enabled: bool) -> Dict:
    """
    Actualiza el estado del agente para una conversación.
    
    Args:
        conversation_id: ID de la conversación
        enabled: True para activar, False para desactivar
        
    Returns:
        Datos de la conversación actualizada
    """
    response = supabase.table("conversations").update(
        {"agent_enabled": enabled, "updated_at": "now()"}
    ).eq("id", conversation_id).execute()
    
    return response.data[0] if response.data else {}

# ----- FUNCIONES ADICIONALES PARA WEBSOCKETS -----

def add_feature_to_requirement(requirement_id: str, feature_data: Dict[str, Any]) -> Dict:
    """
    Añade una feature a un requirement usando los datos proporcionados.
    
    Args:
        requirement_id: ID del requirement
        feature_data: Datos de la feature (name, description)
        
    Returns:
        Datos de la feature creada
    """
    return add_feature(
        requirement_id=requirement_id,
        name=feature_data.get("name"),
        description=feature_data.get("description")
    )

def add_integration_to_requirement(requirement_id: str, integration_data: Dict[str, Any]) -> Dict:
    """
    Añade una integration a un requirement usando los datos proporcionados.
    
    Args:
        requirement_id: ID del requirement
        integration_data: Datos de la integration (name, description)
        
    Returns:
        Datos de la integration creada
    """
    return add_integration(
        requirement_id=requirement_id,
        name=integration_data.get("name"),
        description=integration_data.get("description")
    )
