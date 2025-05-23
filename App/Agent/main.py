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

# Clase para gestionar el contexto global del agente
class AgentContext:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.thread_ids = {}  # Cambiar de una variable simple a un diccionario
        self.current_thread_id = None
        
    def set_thread_id(self, thread_id):
        self.thread_ids[thread_id] = True  # Almacenar en el diccionario
        self.current_thread_id = thread_id  # Establecer como thread_id actual
        logger.info(f"Thread ID configurado: {thread_id}")
        
    def get_thread_id(self):
        if self.current_thread_id is None:
            logger.error("Error: Thread ID no configurado")
            return None
        logger.info(f"Obteniendo thread_id: {self.current_thread_id}")
        return self.current_thread_id

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de timeout (60 segundos)
REQUEST_TIMEOUT = 60

# Importar funciones de outlook.py
from App.Services.outlook import get_available_slots as outlook_get_slots
from App.Services.outlook import schedule_meeting as outlook_schedule
from App.Services.outlook import reschedule_meeting as outlook_reschedule
from App.Services.outlook import cancel_meeting as outlook_cancel
from App.Services.outlook import find_meetings_by_subject as outlook_find_meetings

# Importar funciones de base de datos
from App.DB.db_operations import (
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
    
    # Obtener thread_id del contexto global
    thread_id = AgentContext.get_instance().get_thread_id()
    logger.info(f"process_consent: Usando thread_id {thread_id}")
    
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
    
    # Obtener thread_id del contexto global
    thread_id = AgentContext.get_instance().get_thread_id()
    logger.info(f"save_personal_data: Usando thread_id {thread_id}")
    
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
    # Obtener thread_id del contexto global
    thread_id = AgentContext.get_instance().get_thread_id()
    logger.info(f"save_bant_data: Usando thread_id {thread_id}")
    
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
    # Obtener thread_id del contexto global
    thread_id = AgentContext.get_instance().get_thread_id()
    logger.info(f"save_requirements: Usando thread_id {thread_id}")
    
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
        meeting_subject = "TDX | Demo personalizado - Solución de software a medida"
        meeting_content = (
    "<p>Reunión para presentar un demo personalizado de su solución de software, revisar la cotización y definir los próximos pasos para su implementación con TDX.</p>"
    "<p><strong>Agenda:</strong></p>"
    "<ul>"
    "<li>Presentación del equipo TDX</li>"
    "<li>Demostración funcional personalizada</li>"
    "<li>Validación de requerimientos principales</li>"
    "<li>Presentación de cotización y opciones</li>"
    "<li>Plan de implementación (MVP en 15 días)</li>"
    "<li>Toma de decisiones y próximos pasos</li>"
    "</ul>"
    "<p>Hemos preparado un demo funcional personalizado basado en los requerimientos que nos compartió. Durante esta reunión podrá evaluar la solución y definiremos juntos el plan para implementar su MVP completo en 15 días o menos. No es necesario preparar documentación adicional, nuestro objetivo es mostrarle resultados concretos y facilitar su toma de decisiones.</p>"
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
        # Obtener thread_id del contexto global
        thread_id = AgentContext.get_instance().get_thread_id()
        logger.info(f"schedule_meeting: Usando thread_id {thread_id}")
        
        # Añadir verificación explícita del thread_id
        if not thread_id:
            logger.error("Error: No se pudo obtener thread_id válido para guardar la reunión")
            return format_response("Error al guardar la reunión. Por favor, intenta nuevamente.", "error")
        
        # Buscar usuario y conversación
        user = get_user_by_phone(thread_id)
        logger.info(f"Usuario encontrado: {user is not None}")
        
        if user:
            conversation = get_active_conversation(thread_id)
            logger.info(f"Conversación encontrada: {conversation is not None}")
            
            if conversation:
                # Obtener calificación de lead
                qualification = get_lead_qualification(user["id"], conversation["id"])
                logger.info(f"Calificación de lead encontrada: {qualification is not None}")
                
                if qualification:
                    # Guardar reunión en Supabase
                    try:
                        meeting_result = create_meeting(
                            user_id=user["id"],
                            lead_qualification_id=qualification["id"],
                            outlook_meeting_id=meeting["id"],
                            subject=meeting["subject"],
                            start_time=meeting["start"],
                            end_time=meeting["end"],
                            online_meeting_url=meeting.get("online_meeting", {}).get("join_url")
                        )
                        logger.info(f"Reunión guardada en BD: {meeting_result is not None}")
                        
                        # Actualizar estado
                        update_result = update_lead_qualification(qualification["id"], {
                            "current_step": "completed"
                        })
                        logger.info(f"Estado de calificación actualizado: {update_result is not None}")
                    except Exception as e:
                        logger.error(f"Error al guardar la reunión en la base de datos: {str(e)}")
                        import traceback
                        logger.error(f"Traza completa: {traceback.format_exc()}")
                else:
                    logger.error(f"No se encontró calificación de lead para user_id={user['id']}, conversation_id={conversation['id']}")
            else:
                logger.error(f"No se encontró conversación activa para thread_id={thread_id}")
        else:
            logger.error(f"No se encontró usuario para thread_id={thread_id}")
        
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
def find_meetings(subject_contains: str = "Demo personalizado") -> str:
    """Busca reuniones por parte del asunto.
    
    Args:
        subject_contains: Texto que debe contener el asunto (por defecto "Demo personalizado")
        
    Returns:
        Lista de reuniones que coinciden con el criterio
    """
    try:
        # Obtener thread_id del contexto global
        thread_id = AgentContext.get_instance().get_thread_id()
        logger.info(f"find_meetings: Usando thread_id {thread_id}")
        
        # Si tenemos thread_id, intentar buscar reuniones en la base de datos primero
        if thread_id:
            user = get_user_by_phone(thread_id)
            if user:
                # Buscar reuniones del usuario en la base de datos
                user_meetings = get_user_meetings(user["id"])
                if user_meetings:
                    # Formatear la respuesta para el usuario
                    response = f"Reuniones encontradas para ti:\n\n"
                    
                    for i, meeting in enumerate(user_meetings, 1):
                        response += f"{i}. Asunto: {meeting['subject']}\n"
                        response += f"   Fecha: {meeting['start_time']}\n"
                        response += f"   ID: {meeting['outlook_meeting_id']}\n"
                        
                        if meeting.get('online_meeting_url'):
                            response += f"   Enlace: {meeting['online_meeting_url']}\n"
                        
                        response += "\n"
                    
                    return format_response(response, "meeting")
        
        # Si no encontramos reuniones en la base de datos o no tenemos thread_id,
        # buscar en Outlook usando la API
        meetings = outlook_find_meetings(subject_contains)
        
        if not meetings:
            return format_response(f"No se encontraron reuniones con el asunto '{subject_contains}'.", "warning")
        
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
        
        return format_response(response, "meeting")
    
    except Exception as e:
        logger.error(f"Error al buscar reuniones: {str(e)}")
        import traceback
        logger.error(f"Traza completa: {traceback.format_exc()}")
        return format_response(f"Error al buscar reuniones. Por favor, intenta más tarde.", "error")

@tool
def cancel_meeting(meeting_id: Optional[str] = None) -> str:
    """Cancela una reunión existente.
    
    Args:
        meeting_id: ID de la reunión a cancelar (opcional, si no se proporciona se buscará la reunión del usuario)
        
    Returns:
        Mensaje de confirmación
    """
    try:
        # Si no se proporciona ID, intentar buscar la reunión del usuario
        if not meeting_id:
            # Obtener thread_id del contexto global
            thread_id = AgentContext.get_instance().get_thread_id()
            logger.info(f"cancel_meeting: Usando thread_id {thread_id}")
            
            if not thread_id:
                return format_response("No se pudo identificar al usuario. Por favor, proporciona el ID de la reunión a cancelar.", "error")
            
            # Buscar usuario
            user = get_user_by_phone(thread_id)
            if not user:
                return format_response("No se encontró información del usuario. Por favor, proporciona el ID de la reunión a cancelar.", "error")
            
            # Buscar reuniones del usuario
            user_meetings = get_user_meetings(user["id"])
            if not user_meetings:
                return format_response("No se encontraron reuniones programadas para ti.", "warning")
            
            # Usar la reunión más reciente (asumiendo que es la que quiere cancelar)
            # Ordenar por fecha de inicio (más reciente primero)
            active_meetings = [m for m in user_meetings if m["status"] in ["scheduled", "rescheduled"]]
            if not active_meetings:
                return format_response("No tienes reuniones activas para cancelar.", "warning")
            
            # Ordenar por fecha de inicio (más reciente primero)
            sorted_meetings = sorted(active_meetings, key=lambda x: x["start_time"], reverse=True)
            meeting = sorted_meetings[0]
            meeting_id = meeting["outlook_meeting_id"]
            
            logger.info(f"Se encontró la reunión {meeting_id} para cancelar")
        
        # Cancelar la reunión usando la función de outlook.py
        success = outlook_cancel(meeting_id)
        
        if success:
            # Actualizar estado en la base de datos
            meeting_in_db = get_meeting_by_outlook_id(meeting_id)
            if meeting_in_db:
                # Actualizar estado
                update_meeting_status(meeting_in_db["id"], "cancelled")
            
            logger.info(f"Reunión {meeting_id} cancelada exitosamente")
            return format_response("La reunión ha sido cancelada exitosamente.", "meeting_cancelled")
        else:
            logger.error(f"No se pudo cancelar la reunión {meeting_id}")
            return format_response("No se pudo cancelar la reunión. Por favor, intenta más tarde.", "error")
    
    except Exception as e:
        logger.error(f"Error al cancelar la reunión: {str(e)}")
        import traceback
        logger.error(f"Traza completa: {traceback.format_exc()}")
        return format_response(f"Error al cancelar la reunión. Por favor, intenta más tarde.", "error")

@tool
def reschedule_meeting(meeting_id: Optional[str] = None, new_date: str = None, new_time: str = None, duration: Optional[int] = None) -> str:
    """Reprograma una reunión existente.
    
    Args:
        meeting_id: ID de la reunión a reprogramar (opcional, si no se proporciona se buscará la reunión del usuario)
        new_date: Nueva fecha (múltiples formatos aceptados)
        new_time: Nueva hora (formato 12h o 24h)
        duration: Nueva duración en minutos (opcional)
        
    Returns:
        Mensaje de confirmación con formato visual mejorado
    """
    try:
        # Si no se proporciona fecha o hora, solicitar esta información
        if not new_date or not new_time:
            return format_response("Por favor, indica la nueva fecha y hora para reprogramar la reunión.", "warning")
        
        # Si no se proporciona ID, intentar buscar la reunión del usuario
        if not meeting_id:
            # Obtener thread_id del contexto global
            thread_id = AgentContext.get_instance().get_thread_id()
            logger.info(f"reschedule_meeting: Usando thread_id {thread_id}")
            
            if not thread_id:
                return format_response("No se pudo identificar al usuario. Por favor, proporciona el ID de la reunión a reprogramar.", "error")
            
            # Buscar usuario
            user = get_user_by_phone(thread_id)
            if not user:
                return format_response("No se encontró información del usuario. Por favor, proporciona el ID de la reunión a reprogramar.", "error")
            
            # Buscar reuniones del usuario
            user_meetings = get_user_meetings(user["id"])
            if not user_meetings:
                return format_response("No se encontraron reuniones programadas para ti.", "warning")
            
            # Usar la reunión más reciente (asumiendo que es la que quiere reprogramar)
            # Ordenar por fecha de inicio (más reciente primero)
            active_meetings = [m for m in user_meetings if m["status"] in ["scheduled", "rescheduled"]]
            if not active_meetings:
                return format_response("No tienes reuniones activas para reprogramar.", "warning")
            
            # Ordenar por fecha de inicio (más reciente primero)
            sorted_meetings = sorted(active_meetings, key=lambda x: x["start_time"], reverse=True)
            meeting = sorted_meetings[0]
            meeting_id = meeting["outlook_meeting_id"]
            
            logger.info(f"Se encontró la reunión {meeting_id} para reprogramar")
        
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
    # Inicializar el modelo de OpenAI gpt-4.1-mini con timeout configurado
    model = ChatOpenAI(
        model="gpt-4.1-mini", 
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
        Asistente de Desarrollo de Software a Medida - TDX
DEFINICIÓN DE IDENTIDAD
Eres un asistente virtual que te llamas Matí, especializado en desarrollo de software a medida para empresas TDX. Tu objetivo es asesorar como un arquitecto de software experto y guiar a los clientes a través del proceso de calificación y agendamiento.
DIFERENCIALES DE MERCADO
Menciona naturalmente durante la conversación estos diferenciales:

Velocidad de entrega excepcional: Podemos mostrar un DEMO funcional durante la reunión y entregar un MVP completo en 15 días o menos

Momentos clave para mencionar los diferenciales:

En la presentación inicial: "Podemos mostrarte un DEMO funcional en nuestra primera reunión"
Al hablar de funcionalidades: "Podríamos implementar esas funciones en un MVP en 15 días o menos"
Al agendar la reunión: "Durante la reunión te mostraremos un DEMO de tu solución"

FLUJO DE CONVERSACIÓN
Sigue este orden exacto sin omitir ningún paso:

Presentación inicial - Saluda y preséntate brevemente como Matí, el asistente virtual de TDX
Solicitud de consentimiento - Obtén consentimiento explícito para procesar datos usando process_consent()
Recolección de datos personales - Nombre, empresa, email y teléfono usando save_personal_data()
Cualificación de necesidades y requerimientos - Haz solo 5 preguntas (una a la vez) usando save_bant_data() y save_requirements()
Agendamiento de reunión - Concreta una cita con fecha y hora específicas usando get_available_slots() y schedule_meeting()

HERRAMIENTAS DISPONIBLES
Las siguientes herramientas están disponibles para usar en el flujo:

process_consent(response) - Registra el consentimiento del usuario
save_personal_data(name, company, email, phone) - Guarda los datos personales del cliente
save_bant_data(budget, authority, need, timeline) - Guarda los datos de cualificación
save_requirements(app_type, core_features, integrations, deadline) - Guarda los requerimientos técnicos
get_available_slots(preferred_date=None) - Muestra horarios disponibles
schedule_meeting(email, date=None, time=None, duration=60) - Agenda una reunión con el cliente
find_meetings(subject_contains="Demo personalizado") - Busca reuniones existentes
cancel_meeting(meeting_id=None) - Cancela una reunión programada
reschedule_meeting(meeting_id=None, new_date=None, new_time=None, duration=None) - Reprograma una reunión

COMPORTAMIENTO POR ETAPA

1️⃣ PRESENTACIÓN INICIAL

Saluda cordialmente usando emojis
Preséntate como: "Matí, el asistente virtual de TDX especializado en desarrollo de software a medida"
Menciona brevemente: "podemos mostrarte un DEMO funcional en nuestra primera reunión"
Mantén un tono conversacional, cálido y profesional
IMPORTANTE: Usa emojis naturalmente sin mencionar ninguna función del sistema

2️⃣ SOLICITUD DE CONSENTIMIENTO (OBLIGATORIO)

Solicita explícitamente: "Antes de comenzar, necesito tu consentimiento para procesar tus datos personales e informacion general con el fin de ayudarte mejor con tu proyecto. ¿Me autorizas a recopilar y procesar esta información?"
Espera respuesta afirmativa antes de continuar
Llama a process_consent(respuesta) con la respuesta del usuario
Luego de obtener el consentimiento dejar claro que TDX protege toda la informacion que se comparta en este chat y no la usara para ningun otro fin

3️⃣ RECOLECCIÓN DE DATOS PERSONALES

Solicita: nombre completo, empresa, correo electrónico y teléfono
Verifica que el formato del correo sea válido (debe contener @)
No avances hasta tener todos estos datos
Llama a save_personal_data(nombre, empresa, email, teléfono) con los datos obtenidos

4️⃣ CUALIFICACIÓN DE NECESIDADES Y REQUERIMIENTOS

Haz SOLO UNA pregunta a la vez (nunca múltiples preguntas en un mismo mensaje)
Mantén una conversación ligera y natural, evitando que parezca un interrogatorio
Menciona los diferenciales de forma natural cuando sea relevante
Limita el proceso a estas 5 preguntas esenciales (una por una):

Necesidad: "¿Qué tipo de solución de software estás buscando?" (Ej. Chatbot AI, sistema de inventario, agentes AI, app de reservas, automatizaciones, etc.)

Una vez respondida, guarda esta información y pasa a la siguiente pregunta


Tipo de aplicación: "¿Estás pensando en una solución web, móvil o de escritorio?"

Espera la respuesta y luego avanza a la siguiente pregunta
Podrías mencionar: "Perfecto, tenemos amplia experiencia en [tipo mencionado]"


Funcionalidades e integraciones: "¿Cuáles serían las principales funciones y sistemas con los que debería conectarse?"

Esta pregunta combina funcionalidades e integraciones para reducir el número total de preguntas
Podrías añadir: "Con esas funcionalidades clave, podríamos desarrollar un MVP completo en 15 días o menos"


Plazos: "¿Para cuándo necesitarías tener esto implementado?"

Después de recibir esta respuesta, haz la última pregunta
Si menciona un plazo ajustado: "Entiendo la urgencia. Durante nuestra reunión te mostraremos un DEMO funcional"


Presupuesto y decisores: "Para ajustarnos a tus expectativas, ¿has considerado un rango de inversión? Nuestras soluciones populares suelen estar entre 2.000-15.000 USD. También me ayudaría saber quién suele tomar las decisiones finales sobre este tipo de proyectos en tu empresa."

Esta es la única pregunta que combina dos aspectos para mantener el límite de 5 preguntas




Muestra interés genuino respondiendo brevemente a lo que dice el usuario antes de pasar a la siguiente pregunta
Si las respuestas son muy cortas, haz preguntas de seguimiento amigables
Una vez recopilada toda la información:

Llama a save_bant_data(presupuesto, autoridad, necesidad, tiempo)
Luego llama a save_requirements(tipo_app, funcionalidades, integraciones, fecha_límite)



5️⃣ AGENDAMIENTO DE REUNIÓN

Sugiere reunión como siguiente paso y destaca: "Durante la reunión podremos mostrarte un DEMO funcional de tu solución"
Pregunta por preferencias de fecha y hora (horario laboral L-V, 8am-5pm)
Si el cliente no especifica una fecha, llama a get_available_slots() para mostrar opciones
Si el cliente menciona una fecha, llama a get_available_slots(fecha_preferida) para esa fecha
Cuando el cliente elija fecha y hora, llama a schedule_meeting(email, fecha, hora, duración) para agendar
Confirma la reunión: "Perfecto, ya tenemos agendada la reunión. Prepararemos un DEMO funcional para mostrártelo durante nuestra conversación"
Si el cliente quiere reprogramar, usa reschedule_meeting(meeting_id, nueva_fecha, nueva_hora)
Si el cliente quiere cancelar, usa cancel_meeting(meeting_id)

ESTILO DE COMUNICACIÓN

Usa emojis para hacer respuestas visualmente atractivas
Mantén un tono conversacional y amigable
Divide preguntas complejas en mensajes más cortos
Confirma cada dato proporcionado antes de continuar

NOTA SOBRE EL USO DE FUNCIONES

NUNCA menciones nombres de funciones como "format_response" en tus respuestas
No uses frases como "format_response(...)" en tus mensajes al usuario
Proporciona respuestas naturales con emojis al inicio

REGLAS IMPORTANTES

Habla EXCLUSIVAMENTE sobre desarrollo de software a medida
NO proporciones precios o cotizaciones específicas (se darán en la reunión con el DEMO)
NO avances a la siguiente etapa sin completar la anterior
NO continúes sin consentimiento para procesar datos
Evita lenguaje técnico excesivamente complejo
NO avances sin tener toda la información requerida en cada etapa
NO ofrezcas soluciones técnicas prematuramente
Redirecciona amablemente si la conversación se desvía"""
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
            "content": format_response("💬 ¡Hola! Soy Matí, el asistente virtual de TDX especializado en desarrollo de software a medida. ¿En qué puedo ayudarte hoy?", "general")
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
