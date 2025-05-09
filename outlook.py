"""
Este script permite agendar reuniones en Outlook usando MSAL y Microsoft Graph, incluyendo enlace de Teams.

Requisitos de configuración en Azure AD:
1. Registra la aplicación en App registrations.
2. En **Authentication > Advanced settings**, habilita **Allow public client flows** para Device Code Flow o crea un **Client Secret** para Client Credentials Flow.
3. En **API permissions**, concede:
   - Para Device Code Flow (delegated): **Calendars.ReadWrite** (delegated permissions).
   - Para Client Credentials Flow (app-only): **Calendars.ReadWrite** (application permissions).
4. Para app-only, haz grant de administrador en "Grant admin consent".

Variables de entorno (.env):
- AZURE_CLIENT_ID: ID de la app.
- AZURE_TENANT_ID: ID del tenant.
- AZURE_CLIENT_SECRET: para app-only.
- USER_EMAIL: correo del buzón para app-only.
- TIMEZONE: zona horaria (ej. America/Bogota)

Instalación:
```bash
pip install msal requests python-dotenv pytz
```
"""
import os
import msal
import requests
import pytz
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Importar funciones de base de datos
from db_operations import (
    get_meeting_by_outlook_id,
    update_meeting_status
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de timeout (60 segundos)
REQUEST_TIMEOUT = 60

# Configuración desde variables de entorno
TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
USER_EMAIL = os.getenv("USER_EMAIL", "ventas@tdxcore.com")  # Valor por defecto si no está en .env
TIMEZONE = os.getenv("TIMEZONE", "America/Bogota")  # Valor por defecto si no está en .env

# Scopes
SCOPES_DELEGATED = ["Calendars.ReadWrite"]
SCOPES_APP = ["https://graph.microsoft.com/.default"]
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"


def get_access_token():
    """Obtiene un token de acceso para Microsoft Graph API"""
    start_time = time.time()
    logger.info("Obteniendo token de acceso para Microsoft Graph API")
    
    if not CLIENT_ID or not TENANT_ID:
        logger.error("ERROR: Define CLIENT_ID y TENANT_ID.")
        return None, None
    
    try:
        if CLIENT_SECRET:
            app = msal.ConfidentialClientApplication(CLIENT_ID, client_credential=CLIENT_SECRET, authority=AUTHORITY)
            result = app.acquire_token_for_client(scopes=SCOPES_APP)
            token_type = "app"
        else:
            app = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
            flow = app.initiate_device_flow(scopes=SCOPES_DELEGATED)
            logger.info(flow.get("message"))
            result = app.acquire_token_by_device_flow(flow)
            token_type = "delegated"
        
        if not result or "access_token" not in result:
            logger.error(f"Error obteniendo token: {result.get('error_description')}")
            return None, None
        
        elapsed_time = time.time() - start_time
        logger.info(f"Token obtenido OK ({token_type}) en {elapsed_time:.2f}s")
        return result["access_token"], token_type
    
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error al obtener token después de {elapsed_time:.2f}s: {str(e)}")
        return None, None


def get_available_slots(start_date=None, days=5, start_hour=8, end_hour=17):
    """
    Consulta slots disponibles en el calendario para un rango de fechas.
    
    Args:
        start_date: Fecha de inicio (datetime o None para hoy)
        days: Número de días a consultar
        start_hour: Hora de inicio del día laboral (8 = 8am)
        end_hour: Hora de fin del día laboral (17 = 5pm)
        
    Returns:
        Lista de slots disponibles con formato {date, time, datetime}
    """
    token, token_type = get_access_token()
    if not token:
        return []
    
    # Si no se proporciona fecha de inicio, usar hoy
    bogota_tz = pytz.timezone(TIMEZONE)
    current_time = datetime.now(bogota_tz)
    
    # Asegurar que start_date sea una fecha futura
    if not start_date:
        start_date = current_time
    elif not start_date.tzinfo:
        start_date = bogota_tz.localize(start_date)
    
    # Verificar que la fecha de inicio no sea en el pasado
    if start_date < current_time:
        logger.warning(f"Fecha de inicio {start_date} es en el pasado. Usando fecha actual {current_time}")
        start_date = current_time
    
    # Calcular fecha de fin
    end_date = start_date + timedelta(days=days + 2)  # +2 para compensar fines de semana
    
    # Log para depuración
    logger.info(f"Consultando slots disponibles desde {start_date.strftime('%Y-%m-%d')} hasta {end_date.strftime('%Y-%m-%d')}")
    
    # Formatear fechas para la API
    start_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
    end_str = end_date.strftime("%Y-%m-%dT23:59:59Z")
    
    # Endpoint según tipo de token
    endpoint = f"{GRAPH_ENDPOINT}/me/calendarView?startDateTime={start_str}&endDateTime={end_str}"
    if token_type == "app":
        endpoint = f"{GRAPH_ENDPOINT}/users/{USER_EMAIL}/calendarView?startDateTime={start_str}&endDateTime={end_str}"
    
    # Obtener eventos del calendario con timeout
    try:
        resp = requests.get(
            endpoint,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT
        )
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al obtener eventos después de {REQUEST_TIMEOUT}s")
        return []
    except Exception as e:
        logger.error(f"Error al obtener eventos: {str(e)}")
        return []
    
    if resp.status_code != 200:
        print(f"Error al obtener eventos: {resp.status_code} - {resp.text}")
        return []
    
    # Procesar eventos para determinar slots ocupados
    events = resp.json().get('value', [])
    busy_slots = []
    
    for event in events:
        start_time_str = event.get("start", {}).get("dateTime", "")
        end_time_str = event.get("end", {}).get("dateTime", "")
        
        if start_time_str and end_time_str:
            # Convertir a datetime con zona horaria
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            
            # Convertir a zona horaria de Bogotá
            start_time = start_time.astimezone(bogota_tz)
            end_time = end_time.astimezone(bogota_tz)
            
            busy_slots.append({
                "start": start_time,
                "end": end_time
            })
    
    # Generar slots disponibles (horario de oficina: L-V, 8am-5pm)
    available_slots = []
    current_date = start_date
    days_processed = 0
    
    while days_processed < days:
        # Saltar fines de semana
        if current_date.weekday() < 5:  # 0-4 son lunes a viernes
            # Horario de oficina: slots de 1 hora
            for hour in range(start_hour, end_hour):
                slot_start = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                slot_end = slot_start + timedelta(hours=1)
                
                # Verificar si el slot está disponible
                is_available = True
                for busy in busy_slots:
                    if (slot_start < busy["end"] and slot_end > busy["start"]):
                        is_available = False
                        break
                
                # Si está disponible, añadirlo a la lista
                if is_available:
                    available_slots.append({
                        "date": slot_start.strftime("%Y-%m-%d"),
                        "time": slot_start.strftime("%H:%M"),
                        "datetime": slot_start
                    })
            
            days_processed += 1
        
        # Avanzar al siguiente día
        current_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    return available_slots

def schedule_meeting(subject, start, duration, attendees, body="", is_online_meeting=True):
    """
    Agenda una reunión en el calendario.
    
    Args:
        subject: Asunto de la reunión
        start: Fecha y hora de inicio (datetime)
        duration: Duración en minutos
        attendees: Lista de correos electrónicos de los asistentes
        body: Cuerpo/descripción de la reunión
        is_online_meeting: Si es una reunión online (Teams)
        
    Returns:
        Detalles de la reunión creada o None si falla
    """
    token, token_type = get_access_token()
    if not token:
        return None
    
    # Calcular hora de fin
    end = start + timedelta(minutes=duration)
    
    # Asegurar que start y end tengan zona horaria
    bogota_tz = pytz.timezone(TIMEZONE)
    if not start.tzinfo:
        start = bogota_tz.localize(start)
    if not end.tzinfo:
        end = bogota_tz.localize(end)
    
    # Convertir a UTC para la API
    start_utc = start.astimezone(pytz.UTC)
    end_utc = end.astimezone(pytz.UTC)
    
    # Crear el evento
    event = {
        "subject": subject,
        "body": {
            "contentType": "HTML",
            "content": body
        },
        "start": {
            "dateTime": start_utc.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": end_utc.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": "UTC"
        },
        "attendees": [{"emailAddress": {"address": e, "name": e}, "type": "required"} for e in attendees],
        "isOnlineMeeting": is_online_meeting,
        "onlineMeetingProvider": "teamsForBusiness" if is_online_meeting else None
    }
    
    # Endpoint según tipo de token
    endpoint = f"{GRAPH_ENDPOINT}/me/events"
    if token_type == "app":
        endpoint = f"{GRAPH_ENDPOINT}/users/{USER_EMAIL}/events"
    
    # Crear el evento con timeout
    try:
        resp = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=event,
            timeout=REQUEST_TIMEOUT
        )
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al crear evento después de {REQUEST_TIMEOUT}s")
        return None
    except Exception as e:
        logger.error(f"Error al crear evento: {str(e)}")
        return None
    
    if resp.status_code not in (200, 201):
        print(f"Error al crear evento: {resp.status_code} - {resp.text}")
        return None
    
    # Procesar respuesta
    created_event = resp.json()
    
    # Extraer información relevante
    result = {
        "id": created_event.get("id"),
        "subject": created_event.get("subject"),
        "start": created_event.get("start", {}).get("dateTime"),
        "end": created_event.get("end", {}).get("dateTime"),
        "attendees": [a.get("emailAddress", {}).get("address") for a in created_event.get("attendees", [])],
        "online_meeting": None
    }
    
    # Añadir información de la reunión online si está disponible
    online_meeting = created_event.get("onlineMeeting")
    if online_meeting:
        result["online_meeting"] = {
            "join_url": online_meeting.get("joinUrl"),
            "conference_id": online_meeting.get("conferenceId"),
            "toll_number": online_meeting.get("tollNumber")
        }
    
    return result

def reschedule_meeting(meeting_id, new_start, duration=None):
    """
    Reprograma una reunión existente.
    
    Args:
        meeting_id: ID de la reunión a reprogramar
        new_start: Nueva fecha y hora de inicio (datetime)
        duration: Nueva duración en minutos (opcional, mantiene la duración original si no se especifica)
        
    Returns:
        Detalles de la reunión actualizada o None si falla
    """
    token, token_type = get_access_token()
    if not token:
        return None
    
    # Endpoint según tipo de token
    endpoint = f"{GRAPH_ENDPOINT}/me/events/{meeting_id}"
    if token_type == "app":
        endpoint = f"{GRAPH_ENDPOINT}/users/{USER_EMAIL}/events/{meeting_id}"
    
    # Primero obtener la reunión existente con timeout
    try:
        resp = requests.get(
            endpoint,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT
        )
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al obtener evento para reprogramar después de {REQUEST_TIMEOUT}s")
        return None
    except Exception as e:
        logger.error(f"Error al obtener evento para reprogramar: {str(e)}")
        return None
    
    if resp.status_code != 200:
        print(f"Error al obtener evento: {resp.status_code} - {resp.text}")
        return None
    
    existing_event = resp.json()
    
    # Asegurar que new_start tenga zona horaria
    bogota_tz = pytz.timezone(TIMEZONE)
    if not new_start.tzinfo:
        new_start = bogota_tz.localize(new_start)
    
    # Convertir a UTC para la API
    new_start_utc = new_start.astimezone(pytz.UTC)
    
    # Calcular nueva hora de fin
    if duration is None:
        # Mantener la duración original
        old_start = datetime.fromisoformat(existing_event.get("start", {}).get("dateTime").replace('Z', '+00:00'))
        old_end = datetime.fromisoformat(existing_event.get("end", {}).get("dateTime").replace('Z', '+00:00'))
        original_duration = (old_end - old_start).total_seconds() / 60
        new_end_utc = new_start_utc + timedelta(minutes=original_duration)
    else:
        new_end_utc = new_start_utc + timedelta(minutes=duration)
    
    # Crear el evento actualizado
    update_data = {
        "start": {
            "dateTime": new_start_utc.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": new_end_utc.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": "UTC"
        }
    }
    
    # Actualizar el evento con timeout
    try:
        resp = requests.patch(
            endpoint,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=update_data,
            timeout=REQUEST_TIMEOUT
        )
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al actualizar evento después de {REQUEST_TIMEOUT}s")
        return None
    except Exception as e:
        logger.error(f"Error al actualizar evento: {str(e)}")
        return None
    
    if resp.status_code != 200:
        print(f"Error al actualizar evento: {resp.status_code} - {resp.text}")
        return None
    
    # Procesar respuesta
    updated_event = resp.json()
    
    # Extraer información relevante
    result = {
        "id": updated_event.get("id"),
        "subject": updated_event.get("subject"),
        "start": updated_event.get("start", {}).get("dateTime"),
        "end": updated_event.get("end", {}).get("dateTime"),
        "attendees": [a.get("emailAddress", {}).get("address") for a in updated_event.get("attendees", [])],
        "online_meeting": None
    }
    
    # Añadir información de la reunión online si está disponible
    online_meeting = updated_event.get("onlineMeeting")
    if online_meeting:
        result["online_meeting"] = {
            "join_url": online_meeting.get("joinUrl"),
            "conference_id": online_meeting.get("conferenceId"),
            "toll_number": online_meeting.get("tollNumber")
        }
    
    # Actualizar en Supabase si la reprogramación fue exitosa
    meeting_in_db = get_meeting_by_outlook_id(meeting_id)
    if meeting_in_db:
        # Actualizar estado
        update_meeting_status(meeting_in_db["id"], "rescheduled")
    
    return result

def cancel_meeting(meeting_id):
    """
    Cancela una reunión existente.
    
    Args:
        meeting_id: ID de la reunión a cancelar
        
    Returns:
        True si se canceló correctamente, False si falló
    """
    token, token_type = get_access_token()
    if not token:
        return False
    
    # Endpoint según tipo de token
    endpoint = f"{GRAPH_ENDPOINT}/me/events/{meeting_id}"
    if token_type == "app":
        endpoint = f"{GRAPH_ENDPOINT}/users/{USER_EMAIL}/events/{meeting_id}"
    
    # Eliminar el evento con timeout
    try:
        resp = requests.delete(
            endpoint,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT
        )
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al cancelar evento después de {REQUEST_TIMEOUT}s")
        return False
    except Exception as e:
        logger.error(f"Error al cancelar evento: {str(e)}")
        return False
    
    if resp.status_code != 204:  # 204 No Content es la respuesta esperada para DELETE exitoso
        print(f"Error al cancelar evento: {resp.status_code} - {resp.text}")
        return False
    
    # Actualizar en Supabase si la cancelación fue exitosa
    meeting_in_db = get_meeting_by_outlook_id(meeting_id)
    if meeting_in_db:
        # Actualizar estado
        update_meeting_status(meeting_in_db["id"], "cancelled")
    
    return True

def find_meetings_by_subject(subject_contains, start_date=None, end_date=None):
    """
    Busca reuniones por parte del asunto.
    
    Args:
        subject_contains: Texto que debe contener el asunto
        start_date: Fecha de inicio para la búsqueda (datetime o None para hoy)
        end_date: Fecha de fin para la búsqueda (datetime o None para 30 días después)
        
    Returns:
        Lista de reuniones que coinciden con el criterio
    """
    token, token_type = get_access_token()
    if not token:
        return []
    
    # Si no se proporciona fecha de inicio, usar hoy
    bogota_tz = pytz.timezone(TIMEZONE)
    if not start_date:
        start_date = datetime.now(bogota_tz)
    elif not start_date.tzinfo:
        start_date = bogota_tz.localize(start_date)
    
    # Si no se proporciona fecha de fin, usar 30 días después
    if not end_date:
        end_date = start_date + timedelta(days=30)
    elif not end_date.tzinfo:
        end_date = bogota_tz.localize(end_date)
    
    # Formatear fechas para la API
    start_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
    end_str = end_date.strftime("%Y-%m-%dT23:59:59Z")
    
    # Endpoint según tipo de token
    endpoint = f"{GRAPH_ENDPOINT}/me/calendarView?startDateTime={start_str}&endDateTime={end_str}"
    if token_type == "app":
        endpoint = f"{GRAPH_ENDPOINT}/users/{USER_EMAIL}/calendarView?startDateTime={start_str}&endDateTime={end_str}"
    
    # Obtener eventos del calendario con timeout
    try:
        resp = requests.get(
            endpoint,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=REQUEST_TIMEOUT
        )
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al buscar reuniones después de {REQUEST_TIMEOUT}s")
        return []
    except Exception as e:
        logger.error(f"Error al buscar reuniones: {str(e)}")
        return []
    
    if resp.status_code != 200:
        print(f"Error al obtener eventos: {resp.status_code} - {resp.text}")
        return []
    
    # Filtrar eventos por asunto
    events = resp.json().get('value', [])
    matching_events = []
    
    for event in events:
        event_subject = event.get("subject", "")
        if subject_contains.lower() in event_subject.lower():
            # Convertir fechas a zona horaria local
            start_time_str = event.get("start", {}).get("dateTime", "")
            end_time_str = event.get("end", {}).get("dateTime", "")
            
            if start_time_str and end_time_str:
                # Convertir a datetime con zona horaria
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                
                # Convertir a zona horaria local
                start_time = start_time.astimezone(bogota_tz)
                end_time = end_time.astimezone(bogota_tz)
                
                matching_events.append({
                    "id": event.get("id"),
                    "subject": event_subject,
                    "start": start_time.strftime("%Y-%m-%d %H:%M"),
                    "end": end_time.strftime("%Y-%m-%d %H:%M"),
                    "attendees": [a.get("emailAddress", {}).get("address") for a in event.get("attendees", [])],
                    "online_meeting_url": event.get("onlineMeeting", {}).get("joinUrl") if event.get("onlineMeeting") else None
                })
    
    return matching_events

# Función original para compatibilidad
def schedule_meeting_original(token, token_type, subject, start, duration, attendees):
    """Función original para mantener compatibilidad con código existente"""
    if token_type == "app" and not USER_EMAIL:
        print("ERROR: Define USER_EMAIL para app-only.")
        return
    end = start + timedelta(minutes=duration)
    event = {
        "subject": subject,
        "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
        "end":   {"dateTime": end.isoformat(),   "timeZone": "UTC"},
        "attendees": [{"emailAddress": {"address": e, "name": e}, "type": "required"} for e in attendees],
        # Habilitar reunión en línea de Teams:
        "isOnlineMeeting": True,
        "onlineMeetingProvider": "teamsForBusiness"
    }
    print("Enviando evento (con Teams):", event)
    endpoint = f"{GRAPH_ENDPOINT}/me/events" if token_type == "delegated" else f"{GRAPH_ENDPOINT}/users/{USER_EMAIL}/events"
    resp = requests.post(endpoint,
                         headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                         json=event)
    print(f"HTTP {resp.status_code}: {resp.text}")
    if resp.status_code in (200, 201):
        data = resp.json()
        join_url = data.get("onlineMeeting", {}).get("joinUrl") or data.get("onlineMeetingUrl")
        print(f"Link de Teams: {join_url}")


if __name__ == "__main__":
    print("Iniciando Outlook Scheduler...")
    token, ttype = get_access_token()
    if token:
        start = datetime.utcnow() + timedelta(minutes=10)
        # Usar la nueva función schedule_meeting
        meeting = schedule_meeting(
            subject="Reunión de prueba con Teams",
            start=start,
            duration=30,
            attendees=["freddyrincones@gmail.com"],
            body="<p>Esta es una reunión de prueba creada desde el script outlook.py</p>",
            is_online_meeting=True
        )
        
        if meeting:
            print(f"Reunión creada exitosamente:")
            print(f"  - ID: {meeting.get('id')}")
            print(f"  - Asunto: {meeting.get('subject')}")
            print(f"  - Inicio: {meeting.get('start')}")
            print(f"  - Fin: {meeting.get('end')}")
            print(f"  - Asistentes: {meeting.get('attendees')}")
            
            # Mostrar enlace de Teams si está disponible
            if meeting.get("online_meeting") and meeting["online_meeting"].get("join_url"):
                print(f"  - Link de Teams: {meeting['online_meeting']['join_url']}")
        else:
            print("No se pudo crear la reunión.")
    else:
        print("Fallo al obtener token. Revisa permisos y variables.")
