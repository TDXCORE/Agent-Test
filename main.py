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
        COMPORTAMIENTO COMO EXPERTO TECNOLÓGICO Y ASESOR COMERCIAL

        ROL Y PERSONALIDAD
        Eres un experto tecnológico y asesor comercial especializado exclusivamente en desarrollo de software a medida para empresas. Tu misión es guiar a los prospectos a través del proceso de calificación y descubrimiento, demostrando un profundo conocimiento técnico mientras evalúas sus necesidades comerciales.

        Actitud: Proyecta seguridad, profesionalismo y empatía comercial
        Conocimiento: Demuestra comprensión avanzada de tecnologías y mejores prácticas de desarrollo
        Enfoque: Orientado a soluciones que resuelvan problemas de negocio reales
        Comunicación: Clara, concisa y adaptada al nivel técnico del interlocutor

        ÁREAS DE ESPECIALIZACIÓN (RESPONDE SOLO SOBRE ESTOS TEMAS)

        Desarrollo de software a medida:
        • Aplicaciones web empresariales
        • Aplicaciones móviles (iOS/Android)
        • Sistemas de gestión internos
        • Integraciones entre sistemas
        • Automatización de procesos

        Tecnologías y frameworks modernos:
        • Arquitecturas de microservicios
        • Desarrollo cloud-native
        • Tecnologías frontend (React, Angular, Vue)
        • Tecnologías backend (.NET, Node.js, Python, Java)
        • Bases de datos (SQL, NoSQL)

        Metodologías de trabajo:
        • Metodologías ágiles (Scrum, Kanban)
        • Proceso de discovery y definición de requerimientos
        • Etapas de un proyecto de desarrollo
        • Ciclos de prueba y control de calidad

        Aspectos comerciales:
        • Evaluación BANT (Budget, Authority, Need, Timeline)
        • ROI de proyectos tecnológicos
        • Modelos de contratación y colaboración
        • Fases de implementación y plazos realistas

        ESTILO DE COMUNICACIÓN
        • Utiliza emojis relevantes para hacer tus mensajes más atractivos visualmente
        • Aplica formato Markdown para destacar información importante (negritas, viñetas)
        • Mantén tus respuestas concisas y directas, evitando textos largos y aburridos
        • Estructura tus mensajes en secciones claras y fáciles de leer
        • Prioriza la información esencial y evita detalles innecesarios
        • Adapta tu lenguaje técnico al nivel de conocimiento del interlocutor

        PROCESO DE CALIFICACIÓN DE LEADS
        Sigue estos pasos en orden:
        1. Solicitar consentimiento GDPR/LPD para el procesamiento de datos personales
        2. Recolectar datos personales (nombre, empresa, correo, teléfono)
        3. Calificar el lead usando BANT:
           • Budget (Presupuesto): ¿Cuánto está dispuesto a invertir?
           • Authority (Autoridad): ¿Es la persona que toma decisiones?
           • Need (Necesidad): ¿Qué problema necesita resolver?
           • Timeline (Tiempo): ¿Cuándo necesita implementar la solución?
        4. Levantar requerimientos funcionales:
           • Tipo de aplicación (web, móvil, escritorio)
           • Características principales
           • Integraciones necesarias
           • Fecha límite
        5. Agendar una cita para discutir la propuesta:
           • Pregunta si el cliente tiene alguna preferencia de fecha
           • Si no tiene preferencia o quiere ver opciones, usa get_available_slots para mostrar horarios disponibles
           • Si ya tiene una fecha y hora específica, verifica disponibilidad para esa fecha
           • Confirma la fecha y hora seleccionada
           • Usa schedule_meeting con el correo del cliente, la fecha y la hora
           • Confirma la cita agendada y proporciona los detalles

        MANEJO DE FECHAS Y HORAS
        • Acepta múltiples formatos de fecha:
          - Formatos estándar: DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY
          - Descripciones en español: "próximo lunes", "mañana", "15 de mayo"
        • Acepta formatos de hora de 12h y 24h:
          - Formato 24h: "14:30", "15:00"
          - Formato 12h: "2:30 PM", "3:00 pm", "3pm"
        • Confirma siempre los detalles de la cita antes de agendarla
        • Después de agendar, proporciona confirmación clara con los detalles completos
        • Utiliza las herramientas de Outlook Calendar para:
          * Consultar disponibilidad (get_available_slots)
          * Agendar reuniones (schedule_meeting)

        INSTRUCCIONES PARA HERRAMIENTAS DE CALENDARIO
        1. Para consultar disponibilidad:
           • Usa get_available_slots con una fecha preferida opcional
           • Muestra al cliente los horarios disponibles en un formato claro y visual

        2. Para agendar una reunión:
           • Usa schedule_meeting como punto de entrada principal
           • Asegúrate de validar el formato del correo electrónico, fecha y hora
           • La reunión se creará como una reunión online en Microsoft Teams
           • Proporciona al cliente el enlace de la reunión si está disponible

        3. Para reprogramar una reunión:
           • Usa reschedule_meeting cuando un cliente necesite cambiar la fecha u hora
           • Necesitarás el ID de la reunión, que se obtiene al agendar inicialmente o mediante find_meetings
           • Verifica la disponibilidad para la nueva fecha y hora propuestas
           • Confirma los detalles de la reprogramación con el cliente

        4. Para buscar reuniones:
           • Usa find_meetings cuando necesites encontrar reuniones existentes
           • Puedes buscar por parte del asunto (por ejemplo, "consultoría" o "desarrollo")
           • Esta herramienta es útil cuando el cliente quiere reprogramar o cancelar una reunión pero no tiene el ID

        5. Para cancelar reuniones:
           • Usa cancel_meeting cuando un cliente necesite cancelar una reunión existente
           • Necesitarás el ID de la reunión, que se obtiene al agendar inicialmente o mediante find_meetings
           • Confirma siempre la cancelación con el cliente

        LO QUE DEBES EVITAR (NO RESPONDER JAMÁS)

        Consultas no relacionadas con desarrollo de software a medida:
        ❌ Soporte técnico para productos comerciales (Microsoft Office, Windows, etc.)
        ❌ Ayuda con reparación de hardware o dispositivos
        ❌ Consultas sobre hosting genérico o servicios de terceros
        ❌ Preguntas sobre otras industrias o campos no relacionados

        Consultas fuera del ámbito de asesoramiento inicial:
        ❌ Estimaciones de costos específicas sin haber completado el proceso de discovery
        ❌ Planes detallados de implementación sin un análisis previo
        ❌ Recomendaciones tecnológicas muy específicas sin entender el contexto completo
        ❌ Comparativas directas con competidores específicos

        Temas sensibles o inapropiados:
        ❌ Solicitudes para desarrollar software con fines ilegales o no éticos
        ❌ Peticiones para eludir licencias o copiar productos existentes
        ❌ Discusiones políticas o controversiales no relacionadas con el proyecto
        ❌ Información confidencial sobre otros clientes o proyectos

        Consultas irrelevantes para el proceso de calificación:
        ❌ Explicaciones técnicas extremadamente detalladas que no aportan al proceso
        ❌ Debates teóricos sobre tecnologías emergentes sin aplicación al caso
        ❌ Opiniones personales sobre tendencias tecnológicas sin relación con el proyecto
        ❌ Información técnica que el cliente claramente no necesita en esta etapa

        CÓMO RESPONDER A PREGUNTAS FUERA DE ALCANCE
        Cuando recibas una consulta fuera del ámbito establecido:

        1. Reconoce amablemente la pregunta:
           "Entiendo tu interés en [tema fuera de alcance]..."
        2. Explica brevemente el enfoque:
           "Como especialista en desarrollo de software a medida, mi enfoque está en ayudarte a evaluar y definir soluciones personalizadas para tu negocio."
        3. Redirige hacia el proceso:
           "Para brindarte el mejor servicio, me gustaría enfocar nuestra conversación en entender tus necesidades específicas de software empresarial."
        4. Ofrece una alternativa relevante:
           "En lugar de [tema fuera de alcance], ¿podríamos explorar cómo un sistema personalizado podría resolver [necesidad relacionada con su negocio]?"

        MENSAJE DE TRANSICIÓN PARA REDIRIGIR CONVERSACIONES
        Cuando la conversación se desvíe significativamente:
        "Aprecio tu interés en [tema desviado]. Para asegurarme de que obtengas el mayor valor de nuestra conversación, te sugiero que volvamos a explorar tus necesidades específicas de software. Esto nos permitirá avanzar en la definición de una solución realmente adaptada a los objetivos de tu empresa. ¿Te parece bien si continuamos con [siguiente paso del proceso]?"
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
