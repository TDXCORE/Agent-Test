import os
import json
import datetime
import asyncio
import pytz
import logging
import time
import re
from typing import List, Dict, Optional, Annotated, Any, Tuple, Union
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.checkpoint.memory import InMemorySaver
from langsmith import Client

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de timeout (60 segundos)
REQUEST_TIMEOUT = 60

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

# Funciones auxiliares para manejo de fechas, horas y formato de respuestas
def convert_12h_to_24h(time_str: str) -> str:
    """Convierte una hora en formato 12h (AM/PM) a formato 24h.
    
    Args:
        time_str: Hora en formato 12h (ej: "3:30pm", "10:15 AM", "9 p.m.")
        
    Returns:
        Hora en formato 24h (HH:MM)
    """
    # Normalizar el formato eliminando espacios y convirtiendo a minúsculas
    time_str = time_str.lower().strip().replace(" ", "")
    
    # Patrones para diferentes formatos de hora
    patterns = [
        # 3:30pm, 3:30p.m., 3:30 pm
        r'(\d{1,2}):(\d{2})\s*(?:p\.?m\.?|pm)',
        # 3pm, 3p.m., 3 pm
        r'(\d{1,2})\s*(?:p\.?m\.?|pm)',
        # 3:30am, 3:30a.m., 3:30 am
        r'(\d{1,2}):(\d{2})\s*(?:a\.?m\.?|am)',
        # 3am, 3a.m., 3 am
        r'(\d{1,2})\s*(?:a\.?m\.?|am)',
        # 15:30 (ya en formato 24h)
        r'(\d{1,2}):(\d{2})',
        # 15h, 15h30
        r'(\d{1,2})h(?:(\d{2}))?'
    ]
    
    for pattern in patterns:
        match = re.match(pattern, time_str)
        if match:
            groups = match.groups()
            hour = int(groups[0])
            minute = int(groups[1]) if len(groups) > 1 and groups[1] else 0
            
            # Ajustar hora para PM
            if 'p' in time_str and hour < 12:
                hour += 12
            # Ajustar medianoche para AM
            elif 'a' in time_str and hour == 12:
                hour = 0
                
            # Formatear como HH:MM
            return f"{hour:02d}:{minute:02d}"
    
    # Si no coincide con ningún patrón, devolver el string original
    logger.warning(f"No se pudo convertir la hora: {time_str}")
    return time_str

def parse_date(date_str: str) -> str:
    """Parsea una fecha en múltiples formatos y la convierte a formato YYYY-MM-DD.
    
    Args:
        date_str: Fecha en varios formatos posibles (DD/MM/YYYY, YYYY-MM-DD, texto en español)
        
    Returns:
        Fecha en formato YYYY-MM-DD o None si no se puede parsear
    """
    # Normalizar el formato eliminando espacios extra
    date_str = date_str.strip().lower()
    
    # Obtener fecha actual para referencia
    today = datetime.datetime.now()
    bogota_tz = pytz.timezone("America/Bogota")
    today_local = datetime.datetime.now(bogota_tz).replace(tzinfo=None)
    
    # 1. Intentar formatos estándar
    formats = [
        "%Y-%m-%d",  # YYYY-MM-DD
        "%d/%m/%Y",  # DD/MM/YYYY
        "%d-%m-%Y",  # DD-MM-YYYY
        "%d.%m.%Y",  # DD.MM.YYYY
        "%m/%d/%Y",  # MM/DD/YYYY (formato US)
        "%d/%m/%y",  # DD/MM/YY
        "%Y/%m/%d"   # YYYY/MM/DD
    ]
    
    for fmt in formats:
        try:
            date_obj = datetime.datetime.strptime(date_str, fmt)
            # Asegurarse de que el año sea razonable (actual o futuro)
            if date_obj.year < 100:  # Formato de 2 dígitos para el año
                if date_obj.year < (today.year % 100):
                    date_obj = date_obj.replace(year=date_obj.year + 2000)
                else:
                    date_obj = date_obj.replace(year=date_obj.year + 1900)
            
            # Verificar que la fecha no sea en el pasado
            if date_obj.date() < today.date():
                logger.warning(f"Fecha en el pasado: {date_str}, ajustando al próximo año")
                date_obj = date_obj.replace(year=today.year + 1)
                
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # 2. Intentar con descripciones en español
    descriptions = {
        "hoy": today_local,
        "mañana": today_local + datetime.timedelta(days=1),
        "pasado mañana": today_local + datetime.timedelta(days=2),
        "próximo lunes": today_local + datetime.timedelta((0 - today_local.weekday() + 7) % 7),
        "próximo martes": today_local + datetime.timedelta((1 - today_local.weekday() + 7) % 7),
        "próximo miércoles": today_local + datetime.timedelta((2 - today_local.weekday() + 7) % 7),
        "próximo jueves": today_local + datetime.timedelta((3 - today_local.weekday() + 7) % 7),
        "próximo viernes": today_local + datetime.timedelta((4 - today_local.weekday() + 7) % 7),
        "próximo sábado": today_local + datetime.timedelta((5 - today_local.weekday() + 7) % 7),
        "próximo domingo": today_local + datetime.timedelta((6 - today_local.weekday() + 7) % 7),
        "este lunes": today_local + datetime.timedelta((0 - today_local.weekday()) % 7),
        "este martes": today_local + datetime.timedelta((1 - today_local.weekday()) % 7),
        "este miércoles": today_local + datetime.timedelta((2 - today_local.weekday()) % 7),
        "este jueves": today_local + datetime.timedelta((3 - today_local.weekday()) % 7),
        "este viernes": today_local + datetime.timedelta((4 - today_local.weekday()) % 7),
        "este sábado": today_local + datetime.timedelta((5 - today_local.weekday()) % 7),
        "este domingo": today_local + datetime.timedelta((6 - today_local.weekday()) % 7),
        "lunes": today_local + datetime.timedelta((0 - today_local.weekday() + 7) % 7),
        "martes": today_local + datetime.timedelta((1 - today_local.weekday() + 7) % 7),
        "miércoles": today_local + datetime.timedelta((2 - today_local.weekday() + 7) % 7),
        "jueves": today_local + datetime.timedelta((3 - today_local.weekday() + 7) % 7),
        "viernes": today_local + datetime.timedelta((4 - today_local.weekday() + 7) % 7),
        "sábado": today_local + datetime.timedelta((5 - today_local.weekday() + 7) % 7),
        "domingo": today_local + datetime.timedelta((6 - today_local.weekday() + 7) % 7),
        "lunes próximo": today_local + datetime.timedelta((0 - today_local.weekday() + 7) % 7),
        "martes próximo": today_local + datetime.timedelta((1 - today_local.weekday() + 7) % 7),
        "miércoles próximo": today_local + datetime.timedelta((2 - today_local.weekday() + 7) % 7),
        "jueves próximo": today_local + datetime.timedelta((3 - today_local.weekday() + 7) % 7),
        "viernes próximo": today_local + datetime.timedelta((4 - today_local.weekday() + 7) % 7),
        "sábado próximo": today_local + datetime.timedelta((5 - today_local.weekday() + 7) % 7),
        "domingo próximo": today_local + datetime.timedelta((6 - today_local.weekday() + 7) % 7),
        "en una semana": today_local + datetime.timedelta(days=7),
        "en dos semanas": today_local + datetime.timedelta(days=14),
        "próxima semana": today_local + datetime.timedelta(days=7),
        "siguiente semana": today_local + datetime.timedelta(days=7)
    }
    
    # Buscar coincidencias exactas
    if date_str in descriptions:
        return descriptions[date_str].strftime("%Y-%m-%d")
    
    # Buscar coincidencias parciales
    for key, value in descriptions.items():
        if key in date_str:
            return value.strftime("%Y-%m-%d")
    
    # 3. Intentar extraer patrones de fecha con regex
    # Ejemplo: "el 15 de mayo" o "15 de mayo"
    day_month_pattern = r'(?:el\s+)?(\d{1,2})\s+(?:de\s+)?(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'
    match = re.search(day_month_pattern, date_str)
    if match:
        day = int(match.group(1))
        month_names = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
            "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
        }
        month = month_names[match.group(2)]
        year = today.year
        
        # Si la fecha ya pasó este año, usar el próximo año
        date_obj = datetime.datetime(year, month, day)
        if date_obj.date() < today.date():
            date_obj = date_obj.replace(year=year + 1)
            
        return date_obj.strftime("%Y-%m-%d")
    
    # Si no se pudo parsear, devolver None
    logger.warning(f"No se pudo parsear la fecha: {date_str}")
    return None

def format_response(message: str, response_type: str = "general") -> str:
    """Formatea una respuesta con emojis y Markdown para mejorar la presentación visual.
    
    Args:
        message: Mensaje a formatear
        response_type: Tipo de respuesta para aplicar formato específico
        
    Returns:
        Mensaje formateado con emojis y Markdown
    """
    # Emojis por tipo de respuesta
    emojis = {
        "consent": "✅",
        "personal_data": "👤",
        "bant": "💼",
        "requirements": "📋",
        "meeting": "📅",
        "available_slots": "🕒",
        "meeting_scheduled": "✅📆",
        "meeting_rescheduled": "🔄📆",
        "meeting_cancelled": "❌📆",
        "error": "❗",
        "warning": "⚠️",
        "success": "✅",
        "general": "💬"
    }
    
    # Obtener el emoji adecuado
    emoji = emojis.get(response_type, emojis["general"])
    
    # Reemplazar asteriscos por viñetas reales
    message = re.sub(r'^\s*\*\s+', '• ', message, flags=re.MULTILINE)
    
    # Añadir negrita a títulos y subtítulos
    message = re.sub(r'^([A-Za-zÁÉÍÓÚáéíóúÑñ][A-Za-zÁÉÍÓÚáéíóúÑñ\s]+:)', r'**\1**', message, flags=re.MULTILINE)
    
    # Formatear fechas y horas para destacarlas
    message = re.sub(r'(\d{1,2}/\d{1,2}/\d{4})', r'**\1**', message)
    message = re.sub(r'(\d{1,2}:\d{2})', r'**\1**', message)
    
    # Añadir el emoji al principio del mensaje
    formatted_message = f"{emoji} {message}"
    
    # Asegurar que el mensaje no sea demasiado largo
    # Dividir en párrafos y mantener solo los esenciales
    paragraphs = formatted_message.split('\n\n')
    if len(paragraphs) > 5:
        # Mantener el primer párrafo (introducción) y los últimos 3 (conclusión/acción)
        formatted_message = '\n\n'.join([paragraphs[0]] + paragraphs[-3:])
    
    return formatted_message

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
        return format_response("Gracias por aceptar nuestros términos de procesamiento de datos.", "consent")
    else:
        return format_response("Entendido. Sin su consentimiento, no podemos continuar con el proceso.", "warning")

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
    
    return format_response(f"Datos guardados: {name}, {company}, {email}, {phone}", "personal_data")

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
    
    return format_response(f"Datos BANT guardados: Presupuesto: {budget}, Autoridad: {authority}, Necesidad: {need}, Plazo: {timeline}", "bant")

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
    
    return format_response(f"Requerimientos guardados: Tipo: {app_type}, Características: {core_features}, Integraciones: {integrations}, Fecha límite: {deadline}", "requirements")

@tool
def get_available_slots(preferred_date: Optional[str] = None) -> str:
    """Obtiene slots disponibles para reuniones en horario de oficina (L-V, 8am-5pm).
    
    Args:
        preferred_date: Fecha preferida (múltiples formatos aceptados, opcional)
        
    Returns:
        Lista de slots disponibles con formato visual mejorado
    """
    try:
        # Determinar rango de fechas a consultar
        bogota_tz = pytz.timezone("America/Bogota")
        today = datetime.datetime.now(bogota_tz)
        current_year = today.year
        
        # Log para depuración
        logger.info(f"Fecha actual: {today.strftime('%Y-%m-%d %H:%M:%S')} (Año: {current_year})")
        
        # Fecha mínima para agendar (48 horas después de hoy)
        min_date = today + datetime.timedelta(days=2)
        min_date_str = min_date.strftime("%d/%m/%Y")
        
        # Mensaje inicial
        response_message = ""
        
        if preferred_date:
            # Intentar parsear la fecha en múltiples formatos
            parsed_date = parse_date(preferred_date)
            
            if parsed_date:
                try:
                    start_date = datetime.datetime.strptime(parsed_date, "%Y-%m-%d")
                    
                    # SIEMPRE verificar que el año sea actual o futuro
                    if start_date.year != current_year:
                        logger.warning(f"Fecha preferida {parsed_date} tiene año {start_date.year} diferente al actual {current_year}")
                        start_date = start_date.replace(year=current_year)
                        logger.info(f"Fecha corregida a {start_date.strftime('%Y-%m-%d')}")
                    
                    start_date = bogota_tz.localize(start_date)
                    
                    # Si la fecha es anterior a la fecha mínima, informar al usuario
                    if start_date < min_date:
                        response_message = f"No es posible agendar reuniones para la fecha solicitada. Las reuniones deben agendarse con al menos 48 horas de anticipación (a partir del {min_date_str}).\n\nA continuación te muestro los horarios disponibles más próximos:"
                        # Usar la fecha mínima para consultar disponibilidad
                        start_date = min_date
                    else:
                        response_message = f"Horarios disponibles para el {start_date.strftime('%d/%m/%Y')} y días siguientes:"
                except ValueError:
                    logger.error(f"Error al procesar la fecha parseada: {parsed_date}")
                    response_message = "No pude interpretar correctamente el formato de fecha. A continuación te muestro los horarios disponibles más próximos:"
                    # Usar la fecha mínima para consultar disponibilidad
                    start_date = min_date
            else:
                logger.error(f"No se pudo parsear la fecha: {preferred_date}")
                response_message = "No pude interpretar el formato de fecha proporcionado. A continuación te muestro los horarios disponibles más próximos:"
                # Usar la fecha mínima para consultar disponibilidad
                start_date = min_date
        else:
            # Si no hay fecha preferida, empezar desde la fecha mínima (48h después)
            start_date = min_date
            response_message = f"Horarios disponibles a partir del {min_date_str}:"
        
        # Log para depuración
        logger.info(f"Consultando slots disponibles desde {start_date.strftime('%Y-%m-%d')}")
        
        # Consultar slots disponibles usando la función de outlook.py
        # Mostrar 3 días de disponibilidad a partir de la fecha mínima
        available_slots = outlook_get_slots(start_date=start_date, days=3)
        
        # Log para depuración
        logger.info(f"Slots disponibles encontrados: {len(available_slots)}")
        
        # Si no hay slots disponibles, intentar con fechas posteriores
        if not available_slots:
            # Intentar con los siguientes 5 días
            next_start_date = start_date + datetime.timedelta(days=5)
            logger.info(f"No hay slots disponibles, intentando con fecha: {next_start_date.strftime('%Y-%m-%d')}")
            available_slots = outlook_get_slots(start_date=next_start_date, days=5)
            
            if not available_slots:
                # Si aún no hay slots, intentar con los siguientes 5 días
                next_start_date = next_start_date + datetime.timedelta(days=5)
                logger.info(f"No hay slots disponibles, intentando con fecha: {next_start_date.strftime('%Y-%m-%d')}")
                available_slots = outlook_get_slots(start_date=next_start_date, days=5)
            
            if available_slots:
                response_message += f"\n\nNo hay horarios disponibles para las fechas solicitadas. Te muestro los horarios disponibles a partir del {next_start_date.strftime('%d/%m/%Y')}:"
            else:
                error_msg = "No se encontraron horarios disponibles para las próximas dos semanas. Por favor, contacta directamente con nuestro equipo al correo soporte@tdxcore.com para agendar una reunión personalizada."
                return format_response(error_msg, "warning")
        
        # Verificar que todos los slots sean de fechas futuras
        valid_slots = []
        for slot in available_slots:
            slot_date = datetime.datetime.strptime(slot["date"], "%Y-%m-%d")
            slot_date = bogota_tz.localize(slot_date.replace(hour=int(slot["time"].split(":")[0]), 
                                                           minute=int(slot["time"].split(":")[1])))
            
            # Verificar que la fecha sea futura y posterior a la fecha mínima
            if slot_date >= min_date:
                valid_slots.append(slot)
            else:
                logger.warning(f"Descartando slot en el pasado: {slot['date']} {slot['time']}")
        
        # Usar solo slots válidos
        available_slots = valid_slots
        
        # Agrupar slots por fecha para mejor visualización
        slots_by_date = {}
        for slot in available_slots:
            date = slot["date"]
            if date not in slots_by_date:
                slots_by_date[date] = []
            slots_by_date[date].append(slot["time"])
        
        # Formatear por fecha con mejor presentación visual
        formatted_by_date = []
        for date, times in slots_by_date.items():
            date_obj = datetime.datetime.strptime(date, "%Y-%m-%d")
            day_name = date_obj.strftime("%A")  # Nombre del día
            date_formatted = date_obj.strftime("%d/%m/%Y")
            times_str = ", ".join([f"**{time}**" for time in times])
            formatted_by_date.append(f"• **{day_name} {date_formatted}**: {times_str}")
        
        # Mensaje final con formato mejorado
        final_message = f"{response_message}\n\n{chr(10).join(formatted_by_date)}\n\nPor favor, indícame qué fecha y hora te conviene más para agendar la reunión."
        
        # Aplicar formato visual con emojis
        return format_response(final_message, "available_slots")
    
    except Exception as e:
        logger.error(f"Error al consultar disponibilidad: {str(e)}")
        import traceback
        logger.error(f"Traza completa: {traceback.format_exc()}")
        error_msg = f"Hubo un problema al consultar la disponibilidad. Por favor, intenta nuevamente o indica una fecha específica (por ejemplo, 'próximo lunes' o '15 de mayo')."
        return format_response(error_msg, "error")

@tool
def schedule_meeting(email: str, date: Optional[str] = None, time: Optional[str] = None, duration: int = 60) -> str:
    """Agenda una cita utilizando el calendario de Outlook.
    
    Args:
        email: Correo electrónico del cliente
        date: Fecha propuesta (múltiples formatos aceptados, opcional)
        time: Hora propuesta (formato 12h o 24h, opcional)
        duration: Duración en minutos (por defecto 60)
        
    Returns:
        Mensaje de confirmación o lista de slots disponibles con formato visual mejorado
    """
    try:
        # Validar el formato del correo electrónico
        if not email or "@" not in email:
            return format_response("Por favor, proporciona un correo electrónico válido.", "error")
        
        # Si no se proporciona fecha o hora, mostrar slots disponibles
        if not date or not time:
            return get_available_slots(date)
        
        # Parsear la fecha en múltiples formatos
        parsed_date = parse_date(date)
        if not parsed_date:
            error_msg = f"No pude interpretar el formato de fecha '{date}'. Por favor, indica una fecha válida como '15/05/2025', 'próximo lunes' o '15 de mayo'."
            return format_response(error_msg, "error")
        
        # Convertir hora de formato 12h a 24h si es necesario
        parsed_time = time
        if re.search(r'[aApP]\.?[mM]\.?', time) or re.search(r'\d+\s*[aApP]\.?[mM]\.?', time):
            parsed_time = convert_12h_to_24h(time)
            logger.info(f"Hora convertida de formato 12h a 24h: {time} -> {parsed_time}")
        
        # Validar el formato de la hora
        try:
            time_obj = datetime.datetime.strptime(parsed_time, "%H:%M")
        except ValueError:
            error_msg = f"No pude interpretar el formato de hora '{time}'. Por favor, indica una hora válida como '14:30', '2:30 PM' o '3pm'."
            return format_response(error_msg, "error")
        
        # Validar que la duración sea razonable
        if duration < 15 or duration > 180:
            return format_response("La duración debe estar entre 15 y 180 minutos.", "warning")
        
        # Validar el formato de la fecha
        try:
            date_obj = datetime.datetime.strptime(parsed_date, "%Y-%m-%d")
        except ValueError:
            error_msg = f"Error al procesar la fecha parseada: {parsed_date}. Por favor, intenta con otro formato."
            return format_response(error_msg, "error")
        
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
            message = f"Las reuniones deben agendarse con al menos 48 horas de anticipación (a partir del {min_date.strftime('%d/%m/%Y')}).\n\nA continuación te muestro los horarios disponibles más próximos:"
            return format_response(message, "warning") + "\n\n" + get_available_slots(None)
        
        # Verificar que sea un día laborable (lunes a viernes)
        if start_datetime.weekday() >= 5:  # 5 y 6 son sábado y domingo
            # Encontrar el próximo día laborable
            next_workday = start_datetime
            while next_workday.weekday() >= 5:
                next_workday += datetime.timedelta(days=1)
            
            message = f"Las reuniones solo pueden agendarse en días laborables (lunes a viernes). El {start_datetime.strftime('%d/%m/%Y')} es {start_datetime.strftime('%A')}.\n\nTe sugiero agendar para el próximo día laborable ({next_workday.strftime('%A')} {next_workday.strftime('%d/%m/%Y')}) o elegir entre los siguientes horarios disponibles:"
            return format_response(message, "warning") + "\n\n" + get_available_slots(next_workday.strftime("%Y-%m-%d"))
        
        # Verificar que esté dentro del horario de oficina (8am-5pm)
        if start_datetime.hour < 8 or start_datetime.hour >= 17:
            message = f"Las reuniones solo pueden agendarse en horario de oficina (8:00 - 17:00). La hora solicitada ({parsed_time}) está fuera de este rango.\n\nTe muestro los horarios disponibles para la fecha seleccionada:"
            return format_response(message, "warning") + "\n\n" + get_available_slots(parsed_date)
        
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
            message = f"El horario solicitado ({parsed_date} {parsed_time}) no está disponible.\n\nTe muestro los horarios disponibles para la fecha seleccionada y días cercanos:"
            return format_response(message, "warning") + "\n\n" + get_available_slots(parsed_date)
        
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
            return format_response("No se pudo agendar la reunión. Por favor, intenta más tarde.", "error")
            
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
        response = f"Reunión agendada exitosamente para el {formatted_date} a las {formatted_time}.\n\nSe ha enviado una invitación a {email}."
        
        # Añadir enlace de la reunión si está disponible
        if meeting.get("online_meeting") and meeting["online_meeting"].get("join_url"):
            response += f"\n\nPuedes unirte a la reunión a través de este enlace:\n{meeting['online_meeting']['join_url']}"
        
        return format_response(response, "meeting_scheduled")
    
    except Exception as e:
        logger.error(f"Error al agendar la reunión: {str(e)}")
        import traceback
        logger.error(f"Traza completa: {traceback.format_exc()}")
        error_msg = "Hubo un problema al agendar la reunión. Por favor, intenta nuevamente o contacta con nuestro equipo de soporte."
        return format_response(error_msg, "error")

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
            
            logger.info(f"Reunión {meeting_id} cancelada exitosamente")
            return "La reunión ha sido cancelada exitosamente."
        else:
            logger.error(f"No se pudo cancelar la reunión {meeting_id}")
            return "No se pudo cancelar la reunión. Por favor, verifique el ID de la reunión e intente más tarde."
    
    except Exception as e:
        logger.error(f"Error al cancelar la reunión {meeting_id}: {str(e)}")
        return f"Error al cancelar la reunión: {str(e)}. Por favor, intente más tarde."

@tool
def reschedule_meeting(meeting_id: str, new_date: str, new_time: str, duration: Optional[int] = None) -> str:
    """Reprograma una reunión existente.
    
    Args:
        meeting_id: ID de la reunión a reprogramar
        new_date: Nueva fecha (múltiples formatos aceptados)
        new_time: Nueva hora (formato 12h o 24h)
        duration: Nueva duración en minutos (opcional)
        
    Returns:
        Mensaje de confirmación con formato visual mejorado
    """
    try:
        # Validar el ID de la reunión
        if not meeting_id:
            return format_response("Por favor, proporciona un ID de reunión válido.", "error")
        
        # Parsear la fecha en múltiples formatos
        parsed_date = parse_date(new_date)
        if not parsed_date:
            error_msg = f"No pude interpretar el formato de fecha '{new_date}'. Por favor, indica una fecha válida como '15/05/2025', 'próximo lunes' o '15 de mayo'."
            return format_response(error_msg, "error")
        
        # Convertir hora de formato 12h a 24h si es necesario
        parsed_time = new_time
        if re.search(r'[aApP]\.?[mM]\.?', new_time) or re.search(r'\d+\s*[aApP]\.?[mM]\.?', new_time):
            parsed_time = convert_12h_to_24h(new_time)
            logger.info(f"Hora convertida de formato 12h a 24h: {new_time} -> {parsed_time}")
        
        # Validar el formato de la hora
        try:
            time_obj = datetime.datetime.strptime(parsed_time, "%H:%M")
        except ValueError:
            error_msg = f"No pude interpretar el formato de hora '{new_time}'. Por favor, indica una hora válida como '14:30', '2:30 PM' o '3pm'."
            return format_response(error_msg, "error")
        
        # Validar el formato de la fecha
        try:
            date_obj = datetime.datetime.strptime(parsed_date, "%Y-%m-%d")
        except ValueError:
            error_msg = f"Error al procesar la fecha parseada: {parsed_date}. Por favor, intenta con otro formato."
            return format_response(error_msg, "error")
        
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
            message = f"Las reuniones deben reprogramarse con al menos 48 horas de anticipación (a partir del {min_date.strftime('%d/%m/%Y')}).\n\nA continuación te muestro los horarios disponibles más próximos:"
            return format_response(message, "warning") + "\n\n" + get_available_slots(None)
        
        # Verificar que sea un día laborable (lunes a viernes)
        if new_start_datetime.weekday() >= 5:  # 5 y 6 son sábado y domingo
            # Encontrar el próximo día laborable
            next_workday = new_start_datetime
            while next_workday.weekday() >= 5:
                next_workday += datetime.timedelta(days=1)
            
            message = f"Las reuniones solo pueden agendarse en días laborables (lunes a viernes). El {new_start_datetime.strftime('%d/%m/%Y')} es {new_start_datetime.strftime('%A')}.\n\nTe sugiero reprogramar para el próximo día laborable ({next_workday.strftime('%A')} {next_workday.strftime('%d/%m/%Y')}) o elegir entre los siguientes horarios disponibles:"
            return format_response(message, "warning") + "\n\n" + get_available_slots(next_workday.strftime("%Y-%m-%d"))
        
        # Verificar que esté dentro del horario de oficina (8am-5pm)
        if new_start_datetime.hour < 8 or new_start_datetime.hour >= 17:
            message = f"Las reuniones solo pueden agendarse en horario de oficina (8:00 - 17:00). La hora solicitada ({parsed_time}) está fuera de este rango.\n\nTe muestro los horarios disponibles para la fecha seleccionada:"
            return format_response(message, "warning") + "\n\n" + get_available_slots(parsed_date)
        
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
            message = f"El horario solicitado ({parsed_date} {parsed_time}) no está disponible para reprogramar la reunión.\n\nTe muestro los horarios disponibles para la fecha seleccionada y días cercanos:"
            return format_response(message, "warning") + "\n\n" + get_available_slots(parsed_date)
        
        # Reprogramar la reunión usando la función de outlook.py
        updated_meeting = outlook_reschedule(
            meeting_id=meeting_id,
            new_start=new_start_datetime,
            duration=duration
        )
        
        if not updated_meeting:
            return format_response("No se pudo reprogramar la reunión. Por favor, verifica el ID de la reunión e intenta más tarde.", "error")
            
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
            response += f"\n\nPuedes unirte a la reunión a través de este enlace:\n{updated_meeting['online_meeting']['join_url']}"
        
        return format_response(response, "meeting_rescheduled")
    
    except Exception as e:
        logger.error(f"Error al reprogramar la reunión: {str(e)}")
        import traceback
        logger.error(f"Traza completa: {traceback.format_exc()}")
        error_msg = "Hubo un problema al reprogramar la reunión. Por favor, intenta nuevamente o contacta con nuestro equipo de soporte."
        return format_response(error_msg, "error")

# Función principal para crear el agente
def create_lead_qualification_agent():
    # Inicializar el modelo de OpenAI GPT-4o con timeout configurado
    model = ChatOpenAI(
        model="gpt-4o", 
        temperature=0.2,
        request_timeout=REQUEST_TIMEOUT,
        max_retries=2
    )
    logger.info(f"Modelo OpenAI inicializado con timeout de {REQUEST_TIMEOUT} segundos")
    
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
        Eres un asistente virtual especializado en desarrollo de software a medida para empresas. Tu misión es guiar a los clientes a través del proceso completo de calificación y agendamiento, siguiendo SIEMPRE este flujo obligatorio en orden, sin saltarte ningún paso.

## FLUJO OBLIGATORIO DE CONVERSACIÓN
Debes seguir este flujo paso a paso sin excepción. Cada etapa es OBLIGATORIA y debe completarse antes de pasar a la siguiente:

1. **Presentación inicial** - Saluda y preséntate brevemente
2. **Solicitud de consentimiento** - SIEMPRE debes obtener consentimiento explícito antes de continuar
3. **Recolección completa de datos personales** - Obtén TODOS los datos de contacto
4. **Entendimiento de necesidades** - Recopila TODA la información sobre necesidades del proyecto
5. **Análisis de requerimientos técnicos** - Obtén información completa sobre requerimientos
6. **Agendamiento de reunión** - Concreta una cita con fecha y hora específicas

No puedes saltar ninguna etapa del flujo bajo ninguna circunstancia. Si el cliente intenta saltarse alguna etapa, explica amablemente que necesitas esa información para poder ayudarle mejor.

## COMPORTAMIENTO ESPECÍFICO EN CADA ETAPA

### 1️⃣ PRESENTACIÓN INICIAL
- Saluda cordialmente usando emojis adecuados
- Preséntate como especialista en desarrollo de software a medida
- Menciona brevemente que puedes ayudar a entender sus necesidades y conectarlos con nuestros expertos

### 2️⃣ SOLICITUD DE CONSENTIMIENTO (OBLIGATORIO)
- SIEMPRE como primer paso después de tu presentación, solicita explícitamente el consentimiento
- Usa este mensaje: "Antes de comenzar, necesito tu consentimiento para procesar tus datos personales con el fin de ayudarte mejor con tu proyecto. ¿Me autorizas a recopilar y procesar esta información?"
- Espera respuesta afirmativa antes de continuar
- Usa `process_consent(respuesta)` para registrar la respuesta
- Si no hay consentimiento, no sigas con el resto del proceso

### 3️⃣ RECOLECCIÓN DE DATOS PERSONALES (TODOS OBLIGATORIOS)
- Una vez obtenido el consentimiento, solicita TODOS estos datos específicos:
  * Nombre completo (OBLIGATORIO)
  * Empresa (OBLIGATORIO aunque digas que es opcional al cliente)
  * Correo electrónico (OBLIGATORIO)
  * Teléfono de contacto (OBLIGATORIO)
- No avances a la siguiente etapa hasta tener TODOS estos datos
- Verifica que el formato del correo sea válido (debe contener @)
- Usa `save_personal_data(nombre, empresa, email, teléfono)` para guardar estos datos
- Confirma la recepción de la información de forma amigable
- No puede ser tipo formulario, debe ser muy practico para que no sea aburrido para el cliente

### 4️⃣ ENTENDIMIENTO DE NECESIDADES (TODOS OBLIGATORIOS)
- Pregunta sobre el problema específico a resolver (OBLIGATORIO)
- Pregunta sobre quién toma las decisiones en el proyecto (OBLIGATORIO)
- Pregunta sobre plazos o fechas importantes (OBLIGATORIO)
- Pregunta sobre presupuesto estimado (OBLIGATORIO)
- No avances hasta tener TODA esta información
- Usa `save_bant_data(presupuesto, autoridad, necesidad, tiempo)` para guardar estas respuestas
- No menciones el término "BANT" al cliente en ningún momento
- No puede ser tipo formulario, debe ser muy practico para que no sea aburrido para el cliente

### 5️⃣ ANÁLISIS DE REQUERIMIENTOS TÉCNICOS (TODOS OBLIGATORIOS)
- Pregunta sobre el tipo de aplicación deseada: web, móvil, escritorio (OBLIGATORIO)
- Pregunta sobre funcionalidades principales necesarias (OBLIGATORIO)
- Pregunta sobre integraciones con sistemas existentes (OBLIGATORIO)
- Pregunta sobre la fecha límite para implementación (OBLIGATORIO)
- No avances hasta tener TODA esta información
- Usa `save_requirements(tipo_app, funcionalidades, integraciones, fecha_límite)` para guardar esta información
- No puede ser tipo formulario, debe ser muy practico para que no sea aburrido para el cliente

### 6️⃣ AGENDAMIENTO DE REUNIÓN (OBLIGATORIO)
- Sugiere la reunión como siguiente paso
- Pregunta por preferencias de fecha y hora
- Si no menciona preferencias, usa `get_available_slots()` para mostrar opciones disponibles
- Si menciona una fecha específica, usa `get_available_slots(fecha_preferida)` con esa fecha
- Una vez que el cliente elige una fecha y hora, usa `schedule_meeting(email, fecha, hora, duración)`
- Confirma los detalles finales de la reunión
- Si el cliente desea reprogramar o cancelar, usa las funciones correspondientes
- Usa el formato correcto con emojis y sin asteriscos 

## ESTILO DE COMUNICACIÓN
- Usa emojis en TODAS tus respuestas para hacerlas visualmente atractivas
- NUNCA uses asteriscos (*) para destacar texto
- Usa la función `format_response()` que ya aplica el formato visual correcto
- En lugar de asteriscos, recuerda que `format_response()` ya formatea fechas, horas y títulos
- Mantén un tono conversacional, cálido y profesional
- Divide preguntas complejas en mensajes más cortos y digeribles
- Confirma cada dato proporcionado por el cliente antes de continuar

## ÁREAS DE ESPECIALIZACIÓN
- Desarrollo de software a medida (web, móvil, sistemas de gestión, integraciones)
- Tecnologías y frameworks modernos (microservicios, cloud, React, Angular, .NET, etc.)
- Metodologías de trabajo (ágiles, discovery, pruebas)
- Aspectos comerciales (valor para el negocio, plazos, colaboración)

## LO QUE ESTÁ TOTALMENTE PROHIBIDO HACER

### PROHIBICIONES GENERALES
- ❌ NUNCA uses asteriscos (*) para destacar texto o información
- ❌ NUNCA saltes ninguna etapa del flujo obligatorio
- ❌ NUNCA continúes con el proceso si el cliente no da su consentimiento
- ❌ NUNCA avances a la siguiente etapa si faltan datos obligatorios
- ❌ NUNCA menciones términos técnicos internos como "BANT" o "calificación de leads"
- ❌ NUNCA reveles al cliente que estás siguiendo un proceso estructurado
- ❌ NUNCA crees respuestas que parezcan formularios o cuestionarios
- ❌ NUNCA uses lenguaje técnico excesivamente complejo sin explicarlo

### PROHIBIDO RESPONDER SOBRE ESTOS TEMAS
- ❌ Consultas técnicas no relacionadas con desarrollo de software a medida
- ❌ Soporte técnico para productos comerciales (Microsoft Office, Windows, etc.)
- ❌ Ayuda con reparación de hardware o dispositivos
- ❌ Consultas sobre hosting genérico o servicios de terceros
- ❌ Preguntas sobre otras industrias o campos no relacionados

### PROHIBIDO PROPORCIONAR ESTA INFORMACIÓN
- ❌ Estimaciones de costos específicas sin haber completado el proceso de discovery
- ❌ Planes detallados de implementación sin un análisis previo
- ❌ Recomendaciones tecnológicas muy específicas sin entender el contexto completo
- ❌ Comparativas directas con competidores específicos
- ❌ Información confidencial sobre otros clientes o proyectos

### PROHIBIDO EN REQUERIMIENTOS TÉCNICOS
- ❌ Ofrecer soluciones técnicas prematuramente sin entender completamente las necesidades
- ❌ Entrar en debates técnicos profundos que no son relevantes para la etapa inicial
- ❌ Asumir conocimiento técnico avanzado del cliente
- ❌ Usar jerga técnica sin explicar los conceptos
- ❌ Ignorar las restricciones técnicas mencionadas por el cliente

### PROHIBIDO EN AGENDAMIENTO
- ❌ Sugerir fechas u horas sin verificar disponibilidad real
- ❌ Aceptar fechas en fines de semana o fuera de horario laboral (8am-5pm L-V)
- ❌ Confirmar reuniones sin haber agendado formalmente con `schedule_meeting()`
- ❌ Omitir detalles importantes de la reunión en la confirmación
- ❌ Agendar con menos de 48 horas de anticipación

## MANEJO DE FECHAS Y HORAS
- Las funciones ya manejan múltiples formatos de fecha y hora, así que acepta lo que el cliente te proporcione
- La función `parse_date()` ya procesa expresiones como "próximo lunes" o "15 de mayo"
- La función `convert_12h_to_24h()` ya convierte "3pm" a formato 24h
- Confirma siempre los detalles antes de agendarlos
- Si el cliente proporciona una fecha/hora fuera de horario laboral (L-V, 8am-5pm), explica amablemente las restricciones

## EJEMPLOS DE PREGUNTAS CORRECTAMENTE FORMULADAS

**Para solicitar consentimiento** (SIEMPRE DEBE SER EL PRIMER PASO):
"👋 Antes de comenzar, necesito tu consentimiento para procesar tus datos personales con el fin de ayudarte mejor con tu proyecto. ¿Me autorizas a recopilar y procesar esta información?"

**Para datos de contacto** (TODOS SON OBLIGATORIOS):
"¡Gracias por tu consentimiento! Para poder ayudarte mejor con tu proyecto, necesito algunos datos de contacto. ¿Podrías compartirme tu nombre completo, empresa donde trabajas, correo electrónico y un teléfono de contacto?"

**Para entender necesidades** (TODOS SON OBLIGATORIOS):
"Gracias por compartir tus datos. Ahora me gustaría entender mejor tu proyecto:
¿Qué problema específico estás buscando resolver con este software?
¿Quiénes serán los responsables de tomar decisiones sobre este proyecto?
¿Para cuándo necesitas tener implementada esta solución?
¿Has considerado un rango de presupuesto para este proyecto?"

**Para requerimientos técnicos** (TODOS SON OBLIGATORIOS):
"Excelente. Con esa información, quiero entender los detalles técnicos:
¿Necesitas una aplicación web, móvil o ambas?
¿Cuáles son las funcionalidades principales que debe incluir?
¿Necesitas que se integre con algún sistema que ya utilizas?
¿Cuál sería la fecha límite para tener lista la solución?"

**Para agendamiento** (OBLIGATORIO CONCRETAR UNA CITA):
"El siguiente paso es agendar una reunión con nuestros especialistas. ¿Qué días y horarios te funcionarían mejor? Podemos mostrar nuestra disponibilidad si lo prefieres."

## REDIRECCIÓN DE CONVERSACIONES DESVIADAS
Si el cliente intenta desviarse del flujo o hablar de temas no relacionados:

"Entiendo tu interés en [tema]. Para ayudarte mejor con tu proyecto de software, ¿podríamos continuar con [la etapa actual del proceso]? Esto nos permitirá avanzar más eficientemente en la definición de tu solución."

## FORMATO DE RESPUESTAS
- Usa SIEMPRE la función `format_response(mensaje, tipo_respuesta)` que ya maneja el formato visual y los emojis
- NUNCA añadas asteriscos (*) manualmente para destacar texto
- Los tipos disponibles son: "consent", "personal_data", "bant", "requirements", "meeting", "available_slots", "meeting_scheduled", "meeting_rescheduled", "meeting_cancelled", "error", "warning", "success", "general"

## VERIFICACIÓN DE DATOS
- Si falta algún dato obligatorio, insiste amablemente hasta obtenerlo
- Si el cliente proporciona información incompleta o imprecisa, pide aclaraciones
- No continúes hasta tener TODOS los datos requeridos en cada etapa
- Verifica el formato del correo electrónico antes de usarlo para agendar

## MANEJO DE SITUACIONES ESPECIALES
- Si el cliente se desvía del tema, reconoce su comentario pero vuelve amablemente al flujo obligatorio
- Si el cliente se niega a dar algún dato obligatorio, explica la importancia de esa información
- Si el cliente quiere saltar alguna etapa, explica que necesitas esa información para ofrecer el mejor servicio

IMPORTANTE: NO puedes avanzar a la siguiente etapa hasta haber completado la anterior. Cada paso del flujo es obligatorio y debe seguirse en el orden establecido."
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
    
    # Mensaje inicial con formato mejorado
    messages = [
        {
            "role": "system", 
            "content": "Iniciando conversación con un potencial cliente."
        },
        {
            "role": "assistant", 
            "content": format_response("¡Hola! Soy el asistente virtual especializado en desarrollo de software a medida para empresas. ¿En qué puedo ayudarte hoy?", "general")
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
        
    # Invocar al agente con medición de tiempo
    start_time = time.time()
    logger.info(f"Invocando agente para procesar mensaje: {user_input[:50]}...")
    
    try:
        response = agent.invoke(
            {"messages": messages},
            config
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Agente respondió en {elapsed_time:.2f}s")
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error al invocar agente después de {elapsed_time:.2f}s: {str(e)}")
        # Proporcionar una respuesta de fallback
        response = {
            "messages": messages + [{"role": "assistant", "content": "Lo siento, estoy experimentando dificultades técnicas. Por favor, intenta nuevamente en unos momentos."}]
        }
        
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
