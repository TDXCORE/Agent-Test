import os
import json
import datetime
import asyncio
import pytz
from typing import List, Dict, Optional, Annotated, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.checkpoint.memory import InMemorySaver
from langsmith import Client

# Importar funciones de outlook.py
from outlook import get_available_slots as outlook_get_slots
from outlook import schedule_meeting as outlook_schedule
from outlook import reschedule_meeting as outlook_reschedule
from outlook import cancel_meeting as outlook_cancel
from outlook import find_meetings_by_subject as outlook_find_meetings

# Importar funciones de base de datos
from db_operations import (
    get_user_by_phone,
    get_or_create_user,
    get_active_conversation,
    get_lead_qualification,
    get_or_create_lead_qualification,
    update_lead_qualification,
    create_or_update_bant_data,
    get_or_create_requirements,
    add_feature,
    add_integration,
    create_meeting,
    update_meeting_status,
    get_meeting_by_outlook_id,
    get_user_meetings
)

# Cargar variables de entorno
load_dotenv()

# Configurar LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
langsmith_client = Client()

# Configuración del agente

# Definir modelos de datos
class PersonalData(BaseModel):
    full_name: str
    company: Optional[str] = None
    email: str
    phone: str

class BANTData(BaseModel):
    budget: str
    authority: str
    need: str
    timeline: str

class RequirementsData(BaseModel):
    app_type: str
    core_features: List[str]
    integrations: List[str]
    deadline: str

class LeadQualificationState(AgentState):
    consent: bool = False
    personal_data: Optional[Dict] = Field(default_factory=dict)
    bant_data: Optional[Dict] = Field(default_factory=dict)
    requirements: Optional[Dict] = Field(default_factory=dict)
    meeting_scheduled: bool = False
    current_step: str = "start"

# Definir herramientas
@tool
def process_consent(response: str) -> str:
    """Procesa la respuesta de consentimiento del usuario.
    
    Args:
        response: La respuesta del usuario (sí/no)
        
    Returns:
        Mensaje de confirmación
    """
    # Lógica simple para determinar si el usuario dio consentimiento
    consent_given = response.lower() in ["sí", "si", "yes", "y", "acepto", "estoy de acuerdo"]
    
    # Obtener thread_id del contexto para identificar la conversación
    thread_id = None
    if hasattr(process_consent, "config") and process_consent.config:
        thread_id = process_consent.config.get("thread_id")
    
    if thread_id:
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
    
    if consent_given:
        return "Gracias por aceptar nuestros términos de procesamiento de datos."
    else:
        return "Entendido. Sin su consentimiento, no podemos continuar con el proceso."

@tool
def save_personal_data(name: str, company: Optional[str], email: str, phone: str) -> str:
    """Guarda los datos personales del cliente.
    
    Args:
        name: Nombre completo del cliente
        company: Nombre de la empresa (opcional)
        email: Correo electrónico
        phone: Número de teléfono
        
    Returns:
        Mensaje de confirmación
    """
    # Crear o actualizar usuario en la base de datos
    user = get_or_create_user(
        phone=phone,
        email=email,
        full_name=name,
        company=company
    )
    
    # Obtener thread_id del contexto
    thread_id = None
    if hasattr(save_personal_data, "config") and save_personal_data.config:
        thread_id = save_personal_data.config.get("thread_id")
    
    if thread_id and user:
        # Actualizar conversación si existe
        conversation = get_active_conversation(thread_id)
        if conversation:
            # Actualizar calificación de lead
            qualification = get_or_create_lead_qualification(user["id"], conversation["id"])
            update_lead_qualification(qualification["id"], {
                "current_step": "bant"
            })
    
    return f"Datos guardados: {name}, {company}, {email}, {phone}"

@tool
def save_bant_data(budget: str, authority: str, need: str, timeline: str) -> str:
    """Guarda los datos BANT del cliente.
    
    Args:
        budget: Presupuesto disponible
        authority: Nivel de autoridad para tomar decisiones
        need: Necesidad o problema a resolver
        timeline: Plazo para implementar la solución
        
    Returns:
        Mensaje de confirmación
    """
    # Obtener thread_id del contexto
    thread_id = None
    if hasattr(save_bant_data, "config") and save_bant_data.config:
        thread_id = save_bant_data.config.get("thread_id")
    
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

@tool
def save_requirements(app_type: str, core_features: str, integrations: str, deadline: str) -> str:
    """Guarda los requerimientos del proyecto.
    
    Args:
        app_type: Tipo de aplicación (web, móvil, etc.)
        core_features: Características principales
        integrations: Integraciones necesarias
        deadline: Fecha límite
        
    Returns:
        Mensaje de confirmación
    """
    # Obtener thread_id del contexto
    thread_id = None
    if hasattr(save_requirements, "config") and save_requirements.config:
        thread_id = save_requirements.config.get("thread_id")
    
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

@tool
def get_available_slots(preferred_date: Optional[str] = None) -> str:
    """Obtiene slots disponibles para reuniones en horario de oficina (L-V, 8am-5pm).
    
    Args:
        preferred_date: Fecha preferida (YYYY-MM-DD, opcional)
        
    Returns:
        Lista de slots disponibles
    """
    try:
        # Determinar rango de fechas a consultar
        bogota_tz = pytz.timezone("America/Bogota")
        today = datetime.datetime.now(bogota_tz)
        
        # Fecha mínima para agendar (48 horas después de hoy)
        min_date = today + datetime.timedelta(days=2)
        min_date_str = min_date.strftime("%d/%m/%Y")
        
        # Mensaje inicial
        response_message = ""
        
        if preferred_date:
            # Si hay una fecha preferida, verificar si es válida
            try:
                start_date = datetime.datetime.strptime(preferred_date, "%Y-%m-%d")
                start_date = bogota_tz.localize(start_date)
                
                # Si la fecha es anterior a la fecha mínima, informar al usuario
                if start_date < min_date:
                    response_message = f"Lo siento, no es posible agendar reuniones para la fecha solicitada. Las reuniones deben agendarse con al menos 48 horas de anticipación (a partir del {min_date_str}).\n\nA continuación te muestro los horarios disponibles más próximos:\n\n"
                    # Usar la fecha mínima para consultar disponibilidad
                    start_date = min_date
                else:
                    response_message = f"Horarios disponibles para el {start_date.strftime('%d/%m/%Y')} y días siguientes:\n\n"
            except ValueError:
                response_message = "El formato de fecha proporcionado no es válido. Por favor, utiliza el formato YYYY-MM-DD (por ejemplo, 2025-05-15).\n\nA continuación te muestro los horarios disponibles más próximos:\n\n"
                # Usar la fecha mínima para consultar disponibilidad
                start_date = min_date
        else:
            # Si no hay fecha preferida, empezar desde la fecha mínima (48h después)
            start_date = min_date
            response_message = f"Horarios disponibles a partir del {min_date_str}:\n\n"
        
        # Consultar slots disponibles usando la función de outlook.py
        # Mostrar 3 días de disponibilidad a partir de la fecha mínima
        available_slots = outlook_get_slots(start_date=start_date, days=3)
        
        # Si no hay slots disponibles, intentar con fechas posteriores
        if not available_slots:
            # Intentar con los siguientes 5 días
            next_start_date = start_date + datetime.timedelta(days=5)
            available_slots = outlook_get_slots(start_date=next_start_date, days=5)
            
            if not available_slots:
                # Si aún no hay slots, intentar con los siguientes 5 días
                next_start_date = next_start_date + datetime.timedelta(days=5)
                available_slots = outlook_get_slots(start_date=next_start_date, days=5)
            
            if available_slots:
                response_message += f"No hay horarios disponibles para las fechas solicitadas. Te muestro los horarios disponibles a partir del {next_start_date.strftime('%d/%m/%Y')}:\n\n"
            else:
                return "Lo siento, no se encontraron horarios disponibles para las próximas dos semanas. Por favor, contacta directamente con nuestro equipo al correo soporte@tdxcore.com para agendar una reunión personalizada."
        
        # Formatear la respuesta para el usuario
        formatted_slots = []
        for slot in available_slots:
            date_obj = datetime.datetime.strptime(slot["date"], "%Y-%m-%d")
            day_name = date_obj.strftime("%A")  # Nombre del día
            date_formatted = date_obj.strftime("%d/%m/%Y")
            formatted_slots.append(f"{day_name} {date_formatted} a las {slot['time']}")
        
        # Agrupar slots por fecha para mejor visualización
        slots_by_date = {}
        for slot in available_slots:
            date = slot["date"]
            if date not in slots_by_date:
                slots_by_date[date] = []
            slots_by_date[date].append(slot["time"])
        
        # Formatear por fecha
        formatted_by_date = []
        for date, times in slots_by_date.items():
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
            day_name = date_obj.strftime("%A")  # Nombre del día
            date_formatted = date_obj.strftime("%d/%m/%Y")
            times_str = ", ".join(times)
            formatted_by_date.append(f"- {day_name} {date_formatted}: {times_str}")
        
        return response_message + "\n".join(formatted_by_date) + "\n\nPor favor, indícame qué fecha y hora te conviene más para agendar la reunión."
    
    except Exception as e:
        return f"Lo siento, hubo un problema al consultar la disponibilidad: {str(e)}. Por favor, intenta nuevamente o escribe una fecha específica en formato YYYY-MM-DD (por ejemplo, 2025-05-15)."

@tool
def schedule_meeting(email: str, date: Optional[str] = None, time: Optional[str] = None, duration: int = 60) -> str:
    """Agenda una cita utilizando el calendario de Outlook.
    
    Args:
        email: Correo electrónico del cliente
        date: Fecha propuesta (YYYY-MM-DD, opcional)
        time: Hora propuesta (HH:MM, opcional)
        duration: Duración en minutos (por defecto 60)
        
    Returns:
        Mensaje de confirmación o lista de slots disponibles
    """
    try:
        # Validar el formato del correo electrónico
        if not email or "@" not in email:
            return "Por favor, proporcione un correo electrónico válido."
        
        # Si no se proporciona fecha o hora, mostrar slots disponibles
        if not date or not time:
            return get_available_slots(date)
        
        # Validar el formato de la fecha
        try:
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return "Por favor, proporcione la fecha en formato YYYY-MM-DD (por ejemplo, 2025-05-15)."
        
        # Validar el formato de la hora
        try:
            time_obj = datetime.datetime.strptime(time, "%H:%M")
        except ValueError:
            return "Por favor, proporcione la hora en formato HH:MM (por ejemplo, 14:30)."
        
        # Validar que la duración sea razonable
        if duration < 15 or duration > 180:
            return "La duración debe estar entre 15 y 180 minutos."
        
        # Combinar fecha y hora
        bogota_tz = pytz.timezone("America/Bogota")
        start_datetime = datetime.datetime.combine(
            date_obj.date(), 
            time_obj.time()
        )
        start_datetime = bogota_tz.localize(start_datetime)
        
        # Verificar que la fecha y hora sean al menos 48 horas después de ahora
        min_date = datetime.datetime.now(bogota_tz) + datetime.timedelta(days=2)
        if start_datetime < min_date:
            # En lugar de solo rechazar, ofrecer alternativas
            message = f"Lo siento, las reuniones deben agendarse con al menos 48 horas de anticipación (a partir del {min_date.strftime('%d/%m/%Y')}).\n\n"
            message += "A continuación te muestro los horarios disponibles más próximos:\n\n"
            message += get_available_slots(None)  # Obtener slots disponibles a partir de la fecha mínima
            return message
        
        # Verificar que sea un día laborable (lunes a viernes)
        if start_datetime.weekday() >= 5:  # 5 y 6 son sábado y domingo
            # Encontrar el próximo día laborable
            next_workday = start_datetime
            while next_workday.weekday() >= 5:
                next_workday += datetime.timedelta(days=1)
            
            message = f"Lo siento, las reuniones solo pueden agendarse en días laborables (lunes a viernes). El {start_datetime.strftime('%d/%m/%Y')} es {start_datetime.strftime('%A')}.\n\n"
            message += f"Te sugiero agendar para el próximo día laborable ({next_workday.strftime('%A')} {next_workday.strftime('%d/%m/%Y')}) o elegir entre los siguientes horarios disponibles:\n\n"
            message += get_available_slots(next_workday.strftime("%Y-%m-%d"))
            return message
        
        # Verificar que esté dentro del horario de oficina (8am-5pm)
        if start_datetime.hour < 8 or start_datetime.hour >= 17:
            message = f"Lo siento, las reuniones solo pueden agendarse en horario de oficina (8:00 - 17:00). La hora solicitada ({time}) está fuera de este rango.\n\n"
            message += "Te muestro los horarios disponibles para la fecha seleccionada:\n\n"
            message += get_available_slots(date)
            return message
        
        # Verificar disponibilidad para el horario solicitado
        available_slots = outlook_get_slots(
            start_date=start_datetime.replace(hour=0, minute=0, second=0, microsecond=0),
            days=1
        )
        
        # Verificar si el slot solicitado está en la lista de disponibles
        slot_available = False
        for slot in available_slots:
            slot_datetime = datetime.datetime.strptime(f"{slot['date']} {slot['time']}", "%Y-%m-%d %H:%M")
            slot_datetime = bogota_tz.localize(slot_datetime)
            if slot_datetime == start_datetime:
                slot_available = True
                break
        
        if not slot_available:
            message = f"Lo siento, el horario solicitado ({date} {time}) no está disponible.\n\n"
            message += "Te muestro los horarios disponibles para la fecha seleccionada y días cercanos:\n\n"
            message += get_available_slots(date)
            return message
        
        # Preparar el título y descripción de la reunión
        meeting_subject = "Reunión de consultoría - Desarrollo de software"
        meeting_content = (
            "<p>Reunión para discutir su proyecto de desarrollo de software.</p>"
            "<p><strong>Agenda:</strong></p>"
            "<ul>"
            "<li>Presentación del equipo</li>"
            "<li>Revisión de requerimientos</li>"
            "<li>Discusión de soluciones técnicas</li>"
            "<li>Próximos pasos</li>"
            "</ul>"
            "<p>Por favor, prepare cualquier documentación o preguntas que tenga para la reunión.</p>"
        )
        
        # Agendar la reunión usando la función de outlook.py
        meeting = outlook_schedule(
            subject=meeting_subject,
            start=start_datetime,
            duration=duration,
            attendees=[email],
            body=meeting_content,
            is_online_meeting=True
        )
        
        if not meeting:
            return "No se pudo agendar la reunión. Por favor, intente más tarde."
            
        # Guardar la reunión en la base de datos
        # Obtener thread_id del contexto
        thread_id = None
        if hasattr(schedule_meeting, "config") and schedule_meeting.config:
            thread_id = schedule_meeting.config.get("thread_id")
        
        if thread_id:
            # Buscar usuario y conversación
            user = get_user_by_phone(thread_id)
            if user:
                conversation = get_active_conversation(thread_id)
                if conversation:
                    # Obtener calificación de lead
                    qualification = get_lead_qualification(user["id"], conversation["id"])
                    if qualification:
                        # Guardar reunión en Supabase
                        create_meeting(
                            user_id=user["id"],
                            lead_qualification_id=qualification["id"],
                            outlook_meeting_id=meeting["id"],
                            subject=meeting["subject"],
                            start_time=meeting["start"],
                            end_time=meeting["end"],
                            online_meeting_url=meeting.get("online_meeting", {}).get("join_url")
                        )
                        
                        # Actualizar estado
                        update_lead_qualification(qualification["id"], {
                            "current_step": "completed"
                        })
        
        # Formatear fecha y hora para la respuesta
        formatted_date = start_datetime.strftime("%d/%m/%Y")
        formatted_time = start_datetime.strftime("%H:%M")
        
        # Preparar respuesta
        response = f"Reunión agendada exitosamente para el {formatted_date} a las {formatted_time}. Se ha enviado una invitación a {email}."
        
        # Añadir enlace de la reunión si está disponible
        if meeting.get("online_meeting") and meeting["online_meeting"].get("join_url"):
            response += f"\n\nPuede unirse a la reunión a través de este enlace: {meeting['online_meeting']['join_url']}"
        
        return response
    
    except Exception as e:
        return f"Error al agendar la reunión: {str(e)}. Por favor, intente más tarde o contacte con soporte."

@tool
def find_meetings(subject_contains: str) -> str:
    """Busca reuniones por parte del asunto.
    
    Args:
        subject_contains: Texto que debe contener el asunto
        
    Returns:
        Lista de reuniones que coinciden con el criterio
    """
    try:
        # Buscar reuniones usando la función de outlook.py
        meetings = outlook_find_meetings(subject_contains)
        
        if not meetings:
            return f"No se encontraron reuniones con el asunto '{subject_contains}'."
        
        # Formatear la respuesta para el usuario
        response = f"Reuniones encontradas con el asunto '{subject_contains}':\n\n"
        
        for i, meeting in enumerate(meetings, 1):
            response += f"{i}. Asunto: {meeting['subject']}\n"
            response += f"   Fecha: {meeting['start']}\n"
            response += f"   ID: {meeting['id']}\n"
            response += f"   Asistentes: {', '.join(meeting['attendees'])}\n"
            
            if meeting.get('online_meeting_url'):
                response += f"   Enlace: {meeting['online_meeting_url']}\n"
            
            response += "\n"
        
        return response
    
    except Exception as e:
        return f"Error al buscar reuniones: {str(e)}. Por favor, intente más tarde."

@tool
def cancel_meeting(meeting_id: str) -> str:
    """Cancela una reunión existente.
    
    Args:
        meeting_id: ID de la reunión a cancelar
        
    Returns:
        Mensaje de confirmación
    """
    try:
        # Cancelar la reunión usando la función de outlook.py
        success = outlook_cancel(meeting_id)
        
        if success:
            # Actualizar estado en la base de datos
            meeting_in_db = get_meeting_by_outlook_id(meeting_id)
            if meeting_in_db:
                # Actualizar estado
                update_meeting_status(meeting_in_db["id"], "cancelled")
            
            return "La reunión ha sido cancelada exitosamente."
        else:
            return "No se pudo cancelar la reunión. Por favor, verifique el ID de la reunión e intente más tarde."
    
    except Exception as e:
        return f"Error al cancelar la reunión: {str(e)}. Por favor, intente más tarde."

@tool
def reschedule_meeting(meeting_id: str, new_date: str, new_time: str, duration: Optional[int] = None) -> str:
    """Reprograma una reunión existente.
    
    Args:
        meeting_id: ID de la reunión a reprogramar
        new_date: Nueva fecha (YYYY-MM-DD)
        new_time: Nueva hora (HH:MM)
        duration: Nueva duración en minutos (opcional)
        
    Returns:
        Mensaje de confirmación
    """
    try:
        # Validar el formato de la fecha
        try:
            date_obj = datetime.datetime.strptime(new_date, "%Y-%m-%d")
        except ValueError:
            return "Por favor, proporcione la fecha en formato YYYY-MM-DD (por ejemplo, 2025-05-15)."
        
        # Validar el formato de la hora
        try:
            time_obj = datetime.datetime.strptime(new_time, "%H:%M")
        except ValueError:
            return "Por favor, proporcione la hora en formato HH:MM (por ejemplo, 14:30)."
        
        # Combinar fecha y hora
        bogota_tz = pytz.timezone("America/Bogota")
        new_start_datetime = datetime.datetime.combine(
            date_obj.date(), 
            time_obj.time()
        )
        new_start_datetime = bogota_tz.localize(new_start_datetime)
        
        # Verificar que la fecha y hora sean al menos 48 horas después de ahora
        min_date = datetime.datetime.now(bogota_tz) + datetime.timedelta(days=2)
        if new_start_datetime < min_date:
            # En lugar de solo rechazar, ofrecer alternativas
            message = f"Lo siento, las reuniones deben reprogramarse con al menos 48 horas de anticipación (a partir del {min_date.strftime('%d/%m/%Y')}).\n\n"
            message += "A continuación te muestro los horarios disponibles más próximos:\n\n"
            message += get_available_slots(None)  # Obtener slots disponibles a partir de la fecha mínima
            return message
        
        # Verificar que sea un día laborable (lunes a viernes)
        if new_start_datetime.weekday() >= 5:  # 5 y 6 son sábado y domingo
            # Encontrar el próximo día laborable
            next_workday = new_start_datetime
            while next_workday.weekday() >= 5:
                next_workday += datetime.timedelta(days=1)
            
            message = f"Lo siento, las reuniones solo pueden agendarse en días laborables (lunes a viernes). El {new_start_datetime.strftime('%d/%m/%Y')} es {new_start_datetime.strftime('%A')}.\n\n"
            message += f"Te sugiero reprogramar para el próximo día laborable ({next_workday.strftime('%A')} {next_workday.strftime('%d/%m/%Y')}) o elegir entre los siguientes horarios disponibles:\n\n"
            message += get_available_slots(next_workday.strftime("%Y-%m-%d"))
            return message
        
        # Verificar que esté dentro del horario de oficina (8am-5pm)
        if new_start_datetime.hour < 8 or new_start_datetime.hour >= 17:
            message = f"Lo siento, las reuniones solo pueden agendarse en horario de oficina (8:00 - 17:00). La hora solicitada ({new_time}) está fuera de este rango.\n\n"
            message += "Te muestro los horarios disponibles para la fecha seleccionada:\n\n"
            message += get_available_slots(new_date)
            return message
        
        # Verificar disponibilidad para el horario solicitado
        available_slots = outlook_get_slots(
            start_date=new_start_datetime.replace(hour=0, minute=0, second=0, microsecond=0),
            days=1
        )
        
        # Verificar si el slot solicitado está en la lista de disponibles
        slot_available = False
        for slot in available_slots:
            slot_datetime = datetime.datetime.strptime(f"{slot['date']} {slot['time']}", "%Y-%m-%d %H:%M")
            slot_datetime = bogota_tz.localize(slot_datetime)
            if slot_datetime == new_start_datetime:
                slot_available = True
                break
        
        if not slot_available:
            message = f"Lo siento, el horario solicitado ({new_date} {new_time}) no está disponible para reprogramar la reunión.\n\n"
            message += "Te muestro los horarios disponibles para la fecha seleccionada y días cercanos:\n\n"
            message += get_available_slots(new_date)
            return message
        
        # Reprogramar la reunión usando la función de outlook.py
        updated_meeting = outlook_reschedule(
            meeting_id=meeting_id,
            new_start=new_start_datetime,
            duration=duration
        )
        
        if not updated_meeting:
            return "No se pudo reprogramar la reunión. Por favor, verifique el ID de la reunión e intente más tarde."
            
        # Actualizar estado en la base de datos
        meeting_in_db = get_meeting_by_outlook_id(meeting_id)
        if meeting_in_db:
            # Actualizar estado
            update_meeting_status(meeting_in_db["id"], "rescheduled")
        
        # Formatear fecha y hora para la respuesta
        formatted_date = new_start_datetime.strftime("%d/%m/%Y")
        formatted_time = new_start_datetime.strftime("%H:%M")
        
        # Preparar respuesta
        response = f"Reunión reprogramada exitosamente para el {formatted_date} a las {formatted_time}."
        
        # Añadir enlace de la reunión si está disponible
        if updated_meeting.get("online_meeting") and updated_meeting["online_meeting"].get("join_url"):
            response += f"\n\nPuede unirse a la reunión a través de este enlace: {updated_meeting['online_meeting']['join_url']}"
        
        return response
    
    except Exception as e:
        return f"Error al reprogramar la reunión: {str(e)}. Por favor, intente más tarde o contacte con soporte."

# Función principal para crear el agente
def create_lead_qualification_agent():
    # Inicializar el modelo de OpenAI GPT-4o
    model = ChatOpenAI(model="gpt-4o", temperature=0.2)
    
    # Configurar checkpointer para memoria
    checkpointer = InMemorySaver()
    
    # Definir herramientas
    tools = [
        process_consent,
        save_personal_data,
        save_bant_data,
        save_requirements,
        get_available_slots,
        schedule_meeting,
        reschedule_meeting,
        find_meetings,
        cancel_meeting
    ]
    
    # Crear el agente
    agent = create_react_agent(
        model=model,
        tools=tools,
        checkpointer=checkpointer,
        state_schema=LeadQualificationState,
        prompt="""
        Eres un asistente virtual especializado en calificar leads para una empresa de desarrollo de software.
        Tu objetivo es obtener consentimiento GDPR, recolectar datos del cliente, calificar el lead usando el framework BANT,
        levantar requerimientos funcionales y agendar una cita.
        
        Sigue estos pasos en orden:
        1. Solicitar consentimiento GDPR/LPD para el procesamiento de datos personales
        2. Recolectar datos personales (nombre, empresa, correo, teléfono)
        3. Calificar el lead usando BANT:
           - Budget (Presupuesto): ¿Cuánto está dispuesto a invertir?
           - Authority (Autoridad): ¿Es la persona que toma decisiones?
           - Need (Necesidad): ¿Qué problema necesita resolver?
           - Timeline (Tiempo): ¿Cuándo necesita implementar la solución?
        4. Levantar requerimientos funcionales:
           - Tipo de aplicación (web, móvil, escritorio)
           - Características principales
           - Integraciones necesarias
           - Fecha límite
        5. Agendar una cita para discutir la propuesta:
           - Pregunta si el cliente tiene alguna preferencia de fecha
           - Si no tiene preferencia o quiere ver opciones, usa get_available_slots para mostrar horarios disponibles
           - Si ya tiene una fecha y hora específica, verifica disponibilidad para esa fecha
           - Confirma la fecha y hora seleccionada
           - Usa schedule_meeting con el correo del cliente, la fecha (YYYY-MM-DD), la hora (HH:MM) y duración
           - Confirma la cita agendada y proporciona los detalles
        
        Sé amable, profesional y conciso en tus interacciones. Guía al usuario a través de cada paso
        y utiliza las herramientas disponibles para guardar la información proporcionada.
        
        Importante para el agendamiento de citas:
        - Usa el formato correcto para fechas (YYYY-MM-DD) y horas (HH:MM)
        - Si el cliente no proporciona una fecha específica, muestra opciones de horarios disponibles
        - Confirma siempre los detalles de la cita antes de agendarla
        - Después de agendar, proporciona confirmación clara con los detalles completos
        - Utiliza las herramientas de Outlook Calendar para:
          * Consultar disponibilidad (get_available_slots)
          * Agendar reuniones (schedule_meeting)
        
        Instrucciones específicas para el uso de las herramientas de Outlook Calendar:
        1. Para consultar disponibilidad:
           - Usa get_available_slots con una fecha preferida opcional
           - Muestra al cliente los horarios disponibles en un formato claro
        
        2. Para agendar una reunión:
           - Usa schedule_meeting como punto de entrada principal
           - Asegúrate de validar el formato del correo electrónico, fecha y hora
           - La reunión se creará como una reunión online en Microsoft Teams
           - Proporciona al cliente el enlace de la reunión si está disponible
        
        3. Para reprogramar una reunión:
           - Usa reschedule_meeting cuando un cliente necesite cambiar la fecha u hora de una reunión existente
           - Necesitarás el ID de la reunión, que se obtiene al agendar inicialmente o mediante find_meetings
           - Verifica la disponibilidad para la nueva fecha y hora propuestas
           - Confirma los detalles de la reprogramación con el cliente
        
        4. Para buscar reuniones:
           - Usa find_meetings cuando necesites encontrar reuniones existentes
           - Puedes buscar por parte del asunto (por ejemplo, "consultoría" o "desarrollo")
           - Esta herramienta es útil cuando el cliente quiere reprogramar o cancelar una reunión pero no tiene el ID
        
        5. Para cancelar reuniones:
           - Usa cancel_meeting cuando un cliente necesite cancelar una reunión existente
           - Necesitarás el ID de la reunión, que se obtiene al agendar inicialmente o mediante find_meetings
           - Confirma siempre la cancelación con el cliente
        
        6. Manejo de errores:
           - Si hay algún error al consultar disponibilidad, agendar, reprogramar o cancelar, informa al cliente
           - Ofrece alternativas o solicita que intente nuevamente
        """
    )
    
    return agent

# Función para ejecutar una conversación interactiva en la terminal
def run_interactive_terminal():
    print("Inicializando agente de calificación de leads...")
    agent = create_lead_qualification_agent()
    
    # Configuración para la ejecución
    config = {
        "configurable": {
            "thread_id": "1"  # ID de conversación
        }
    }
    
    # Mensaje inicial
    messages = [
        {
            "role": "system", 
            "content": "Iniciando conversación con un potencial cliente."
        },
        {
            "role": "assistant", 
            "content": "¡Hola! Soy el asistente virtual de nuestra empresa de desarrollo de software. ¿En qué puedo ayudarte hoy?"
        }
    ]
    
    print("\n" + messages[1]["content"])
    
    # Bucle de conversación
    while True:
        # Obtener entrada del usuario
        user_input = input("\nTú: ")
        
        if user_input.lower() in ["salir", "exit", "quit", "q"]:
            print("\nFinalizando conversación. ¡Gracias!")
            break
        
        # Añadir mensaje del usuario
        messages.append({"role": "user", "content": user_input})
        
        # Invocar al agente
        response = agent.invoke(
            {"messages": messages},
            config
        )
        
        # Actualizar mensajes con la respuesta
        messages = response["messages"]
        
        # Mostrar la respuesta del asistente
        assistant_message = messages[-1]
        # Acceder al contenido del mensaje de manera segura
        if hasattr(assistant_message, "content"):
            # Si es un objeto de mensaje de LangChain
            content = assistant_message.content
        elif isinstance(assistant_message, dict) and "content" in assistant_message:
            # Si es un diccionario
            content = assistant_message["content"]
        else:
            # Fallback
            content = str(assistant_message)
        
        print(f"\nAsistente: {content}")

# Punto de entrada para ejecutar el agente desde la terminal
if __name__ == "__main__":
    run_interactive_terminal()
