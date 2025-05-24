"""
Handler para operaciones de meetings vía WebSocket.
"""

from typing import Dict, Any, List, Optional
import logging
from .base import BaseHandler
from ..events.dispatcher import dispatch_event
import asyncio
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MeetingsHandler(BaseHandler):
    """Handler para operaciones de meetings."""
    
    def _register_actions(self) -> None:
        """Registra los manejadores de acciones para meetings."""
        self.action_handlers = {
            "get_all_meetings": self.get_all_meetings,
            "get_calendar_view": self.get_calendar_view,
            "create_meeting": self.create_meeting,
            "update_meeting": self.update_meeting,
            "cancel_meeting": self.cancel_meeting,
            "get_available_slots": self.get_available_slots,
            "sync_outlook_calendar": self.sync_outlook_calendar
        }
    
    # Función auxiliar para convertir funciones síncronas en asíncronas
    def to_async(self, func):
        @wraps(func)
        async def run(*args, **kwargs):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        return run
    
    async def get_all_meetings(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene todas las meetings con filtros."""
        filter_type = payload.get("filter", "all")  # all, today, this_week, by_status
        status = payload.get("status")  # scheduled, completed, cancelled
        limit = payload.get("limit", 50)
        offset = payload.get("offset", 0)
        
        # Obtener meetings con filtros
        meetings = await self.to_async(self._get_meetings_with_filters)(filter_type, status, limit, offset)
        
        return {
            "meetings": meetings,
            "filter": filter_type,
            "status": status,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(meetings)
            }
        }
    
    async def get_calendar_view(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene vista de calendario agrupada por fecha."""
        start_date = payload.get("start_date")  # YYYY-MM-DD
        end_date = payload.get("end_date")    # YYYY-MM-DD
        
        if not start_date or not end_date:
            # Default: próximos 30 días
            now = datetime.now()
            start_date = now.strftime("%Y-%m-%d")
            end_date = (now + timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Obtener vista de calendario
        calendar_data = await self.to_async(self._get_calendar_view_data)(start_date, end_date)
        
        return {
            "calendar": calendar_data,
            "start_date": start_date,
            "end_date": end_date,
            "generated_at": datetime.now().isoformat()
        }
    
    async def create_meeting(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Crea una nueva meeting usando outlook.py."""
        meeting_data = payload.get("meeting")
        
        if not meeting_data:
            raise ValueError("Se requieren datos de meeting")
        
        # Validar datos requeridos
        required_fields = ["user_id", "subject", "start_time", "end_time"]
        for field in required_fields:
            if not meeting_data.get(field):
                raise ValueError(f"Campo requerido: {field}")
        
        # Crear meeting usando outlook.py
        new_meeting = await self.to_async(self._create_meeting_with_outlook)(meeting_data)
        
        # Notificar sobre la nueva meeting
        await dispatch_event("meeting_created", {
            "meeting": new_meeting
        })
        
        return {
            "meeting": new_meeting
        }
    
    async def update_meeting(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza una meeting existente."""
        meeting_id = payload.get("meeting_id")
        meeting_data = payload.get("meeting")
        
        if not meeting_id or not meeting_data:
            raise ValueError("Se requieren meeting_id y datos de meeting")
        
        # Actualizar meeting y sincronizar con Outlook
        updated_meeting = await self.to_async(self._update_meeting_with_outlook)(meeting_id, meeting_data)
        
        # Notificar sobre la actualización
        await dispatch_event("meeting_updated", {
            "meeting_id": meeting_id,
            "meeting": updated_meeting
        })
        
        return {
            "meeting": updated_meeting
        }
    
    async def cancel_meeting(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Cancela una meeting."""
        meeting_id = payload.get("meeting_id")
        reason = payload.get("reason", "Cancelada por el usuario")
        
        if not meeting_id:
            raise ValueError("Se requiere meeting_id")
        
        # Cancelar meeting usando outlook.py
        cancelled_meeting = await self.to_async(self._cancel_meeting_with_outlook)(meeting_id, reason)
        
        # Notificar sobre la cancelación
        await dispatch_event("meeting_cancelled", {
            "meeting_id": meeting_id,
            "meeting": cancelled_meeting,
            "reason": reason
        })
        
        return {
            "meeting": cancelled_meeting,
            "cancelled": True,
            "reason": reason
        }
    
    async def get_available_slots(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene slots disponibles usando outlook.py."""
        date = payload.get("date")  # YYYY-MM-DD
        duration_minutes = payload.get("duration_minutes", 60)
        
        if not date:
            raise ValueError("Se requiere fecha")
        
        # Obtener slots disponibles
        available_slots = await self.to_async(self._get_available_slots_from_outlook)(date, duration_minutes)
        
        return {
            "available_slots": available_slots,
            "date": date,
            "duration_minutes": duration_minutes
        }
    
    async def sync_outlook_calendar(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sincroniza el calendario con Outlook."""
        sync_direction = payload.get("direction", "bidirectional")  # import, export, bidirectional
        days_range = payload.get("days_range", 30)
        
        # Realizar sincronización
        sync_result = await self.to_async(self._sync_with_outlook)(sync_direction, days_range)
        
        return {
            "sync_result": sync_result,
            "direction": sync_direction,
            "days_range": days_range,
            "synced_at": datetime.now().isoformat()
        }
    
    def _get_meetings_with_filters(self, filter_type: str, status: Optional[str] = None, 
                                  limit: int = 50, offset: int = 0) -> List[Dict]:
        """Función auxiliar para obtener meetings con filtros."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Query base con JOINs
        query = supabase.table("meetings").select("""
            *,
            users(full_name, email, phone, company),
            lead_qualification(current_step, consent)
        """)
        
        # Aplicar filtros de fecha
        now = datetime.now()
        if filter_type == "today":
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            query = query.gte("start_time", today_start.isoformat()).lt("start_time", today_end.isoformat())
        elif filter_type == "this_week":
            week_start = now - timedelta(days=now.weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            week_end = week_start + timedelta(days=7)
            query = query.gte("start_time", week_start.isoformat()).lt("start_time", week_end.isoformat())
        
        # Aplicar filtro de status
        if status:
            query = query.eq("status", status)
        
        response = query.order("start_time", desc=True).range(offset, offset + limit - 1).execute()
        
        return response.data if response.data else []
    
    def _get_calendar_view_data(self, start_date: str, end_date: str) -> Dict[str, List[Dict]]:
        """Función auxiliar para obtener vista de calendario."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Convertir fechas a datetime para comparación
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        
        # Obtener meetings en el rango de fechas
        response = supabase.table("meetings").select("""
            *,
            users(full_name, email, phone),
            lead_qualification(current_step)
        """).gte("start_time", start_datetime.isoformat()).lt(
            "start_time", end_datetime.isoformat()
        ).order("start_time", desc=False).execute()
        
        meetings = response.data if response.data else []
        
        # Agrupar por fecha
        calendar_data = {}
        
        for meeting in meetings:
            # Extraer fecha del start_time
            meeting_date = datetime.fromisoformat(meeting["start_time"].replace('Z', '+00:00')).strftime("%Y-%m-%d")
            
            if meeting_date not in calendar_data:
                calendar_data[meeting_date] = []
            
            calendar_data[meeting_date].append(meeting)
        
        # Asegurar que todas las fechas en el rango estén representadas
        current_date = start_datetime
        while current_date < end_datetime:
            date_str = current_date.strftime("%Y-%m-%d")
            if date_str not in calendar_data:
                calendar_data[date_str] = []
            current_date += timedelta(days=1)
        
        return calendar_data
    
    def _create_meeting_with_outlook(self, meeting_data: Dict[str, Any]) -> Dict:
        """Función auxiliar para crear meeting con Outlook."""
        from App.Services.outlook import create_meeting
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        try:
            # Crear meeting en Outlook
            outlook_meeting = create_meeting(
                subject=meeting_data["subject"],
                start_time=meeting_data["start_time"],
                end_time=meeting_data["end_time"],
                attendees=meeting_data.get("attendees", []),
                body=meeting_data.get("body", "")
            )
            
            # Preparar datos para la BD
            db_meeting_data = {
                "user_id": meeting_data["user_id"],
                "lead_qualification_id": meeting_data.get("lead_qualification_id"),
                "outlook_meeting_id": outlook_meeting.get("id"),
                "subject": meeting_data["subject"],
                "start_time": meeting_data["start_time"],
                "end_time": meeting_data["end_time"],
                "status": "scheduled",
                "online_meeting_url": outlook_meeting.get("onlineMeeting", {}).get("joinUrl"),
                "created_at": datetime.now().isoformat()
            }
            
            # Guardar en BD
            response = supabase.table("meetings").insert(db_meeting_data).execute()
            
            if response.data:
                return response.data[0]
            else:
                raise Exception("Error al guardar meeting en BD")
                
        except Exception as e:
            logger.error(f"Error creando meeting: {str(e)}")
            # Si falla Outlook, crear solo en BD
            db_meeting_data = {
                "user_id": meeting_data["user_id"],
                "lead_qualification_id": meeting_data.get("lead_qualification_id"),
                "subject": meeting_data["subject"],
                "start_time": meeting_data["start_time"],
                "end_time": meeting_data["end_time"],
                "status": "scheduled",
                "created_at": datetime.now().isoformat()
            }
            
            response = supabase.table("meetings").insert(db_meeting_data).execute()
            return response.data[0] if response.data else {}
    
    def _update_meeting_with_outlook(self, meeting_id: str, meeting_data: Dict[str, Any]) -> Dict:
        """Función auxiliar para actualizar meeting con Outlook."""
        from App.Services.outlook import update_meeting
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Obtener meeting actual
        current_meeting = supabase.table("meetings").select("*").eq("id", meeting_id).execute()
        
        if not current_meeting.data:
            raise ValueError("Meeting no encontrada")
        
        meeting = current_meeting.data[0]
        
        try:
            # Actualizar en Outlook si tiene outlook_meeting_id
            if meeting.get("outlook_meeting_id"):
                update_meeting(
                    meeting_id=meeting["outlook_meeting_id"],
                    subject=meeting_data.get("subject", meeting["subject"]),
                    start_time=meeting_data.get("start_time", meeting["start_time"]),
                    end_time=meeting_data.get("end_time", meeting["end_time"]),
                    body=meeting_data.get("body", "")
                )
        except Exception as e:
            logger.error(f"Error actualizando meeting en Outlook: {str(e)}")
        
        # Actualizar en BD
        update_data = {
            **meeting_data,
            "updated_at": datetime.now().isoformat()
        }
        
        response = supabase.table("meetings").update(update_data).eq("id", meeting_id).execute()
        
        return response.data[0] if response.data else {}
    
    def _cancel_meeting_with_outlook(self, meeting_id: str, reason: str) -> Dict:
        """Función auxiliar para cancelar meeting con Outlook."""
        from App.Services.outlook import cancel_meeting_wrapper
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Obtener meeting actual
        current_meeting = supabase.table("meetings").select("*").eq("id", meeting_id).execute()
        
        if not current_meeting.data:
            raise ValueError("Meeting no encontrada")
        
        meeting = current_meeting.data[0]
        
        try:
            # Cancelar en Outlook si tiene outlook_meeting_id
            if meeting.get("outlook_meeting_id"):
                cancel_meeting_wrapper(meeting["outlook_meeting_id"], reason)
        except Exception as e:
            logger.error(f"Error cancelando meeting en Outlook: {str(e)}")
        
        # Actualizar status en BD
        update_data = {
            "status": "cancelled",
            "updated_at": datetime.now().isoformat()
        }
        
        response = supabase.table("meetings").update(update_data).eq("id", meeting_id).execute()
        
        return response.data[0] if response.data else {}
    
    def _get_available_slots_from_outlook(self, date: str, duration_minutes: int) -> List[Dict]:
        """Función auxiliar para obtener slots disponibles de Outlook."""
        from App.Services.outlook import get_available_slots_wrapper
        
        try:
            # Obtener slots disponibles de Outlook usando wrapper
            slots = get_available_slots_wrapper(date, duration_minutes)
            return slots
        except Exception as e:
            logger.error(f"Error obteniendo slots de Outlook: {str(e)}")
            
            # Fallback: generar slots básicos (9 AM - 5 PM, cada hora)
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            available_slots = []
            
            for hour in range(9, 17):  # 9 AM a 5 PM
                slot_start = date_obj.replace(hour=hour, minute=0, second=0, microsecond=0)
                slot_end = slot_start + timedelta(minutes=duration_minutes)
                
                available_slots.append({
                    "start_time": slot_start.isoformat(),
                    "end_time": slot_end.isoformat(),
                    "available": True
                })
            
            return available_slots
    
    def _sync_with_outlook(self, sync_direction: str, days_range: int) -> Dict[str, Any]:
        """Función auxiliar para sincronizar con Outlook."""
        from App.Services.outlook import sync_calendar
        
        try:
            # Realizar sincronización usando outlook.py
            sync_result = sync_calendar()
            
            return {
                "success": True,
                "synced_events": sync_result.get("synced_events", 0),
                "updated_events": sync_result.get("updated_events", 0),
                "new_events": sync_result.get("new_events", 0),
                "total_events": sync_result.get("total_events", 0),
                "errors": sync_result.get("errors", [])
            }
            
        except Exception as e:
            logger.error(f"Error en sincronización con Outlook: {str(e)}")
            
            return {
                "success": False,
                "error": str(e),
                "synced_events": 0,
                "updated_events": 0,
                "new_events": 0,
                "total_events": 0
            }
