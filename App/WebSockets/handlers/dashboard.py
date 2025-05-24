"""
Handler para operaciones del dashboard vía WebSocket.
"""

from typing import Dict, Any, List, Optional
import logging
from .base import BaseHandler
from ..events.dispatcher import dispatch_event
import asyncio
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DashboardHandler(BaseHandler):
    """Handler para operaciones del dashboard."""
    
    def _register_actions(self) -> None:
        """Registra los manejadores de acciones para dashboard."""
        self.action_handlers = {
            "get_dashboard_stats": self.get_dashboard_stats,
            "get_conversion_funnel": self.get_conversion_funnel,
            "get_activity_timeline": self.get_activity_timeline,
            "get_agent_performance": self.get_agent_performance,
            "get_real_time_metrics": self.get_real_time_metrics
        }
    
    # Función auxiliar para convertir funciones síncronas en asíncronas
    def to_async(self, func):
        @wraps(func)
        async def run(*args, **kwargs):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        return run
    
    async def get_dashboard_stats(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene estadísticas generales del dashboard."""
        date_range = payload.get("date_range", "today")  # today, week, month, all
        
        # Obtener métricas generales
        stats = await self.to_async(self._get_dashboard_metrics)(date_range)
        
        return {
            "stats": stats,
            "date_range": date_range,
            "generated_at": datetime.now().isoformat()
        }
    
    async def get_conversion_funnel(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene datos del funnel de conversión."""
        date_range = payload.get("date_range", "all")
        
        # Obtener datos del funnel
        funnel_data = await self.to_async(self._get_conversion_funnel_data)(date_range)
        
        return {
            "funnel": funnel_data,
            "date_range": date_range,
            "generated_at": datetime.now().isoformat()
        }
    
    async def get_activity_timeline(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene timeline de actividad reciente."""
        hours = payload.get("hours", 24)
        
        # Obtener actividad reciente
        timeline = await self.to_async(self._get_activity_timeline)(hours)
        
        return {
            "timeline": timeline,
            "hours": hours,
            "generated_at": datetime.now().isoformat()
        }
    
    async def get_agent_performance(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene métricas de performance del agente IA."""
        date_range = payload.get("date_range", "week")
        
        # Obtener performance del agente
        performance = await self.to_async(self._get_agent_performance_stats)(date_range)
        
        return {
            "agent_performance": performance,
            "date_range": date_range,
            "generated_at": datetime.now().isoformat()
        }
    
    async def get_real_time_metrics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene métricas en tiempo real."""
        # Obtener métricas en tiempo real
        metrics = await self.to_async(self._get_real_time_metrics)()
        
        return {
            "real_time_metrics": metrics,
            "generated_at": datetime.now().isoformat()
        }
    
    def _get_dashboard_metrics(self, date_range: str) -> Dict[str, Any]:
        """Función auxiliar para obtener métricas del dashboard."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Calcular fechas según el rango
        now = datetime.now()
        if date_range == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == "week":
            start_date = now - timedelta(days=7)
        elif date_range == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = None
        
        # Total de usuarios
        users_query = supabase.table("users").select("id", count="exact")
        if start_date:
            users_query = users_query.gte("created_at", start_date.isoformat())
        total_users = users_query.execute().count or 0
        
        # Conversaciones activas
        conv_query = supabase.table("conversations").select("id", count="exact").eq("status", "active")
        if start_date:
            conv_query = conv_query.gte("created_at", start_date.isoformat())
        active_conversations = conv_query.execute().count or 0
        
        # Meetings de hoy
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        meetings_today = supabase.table("meetings").select("id", count="exact").gte(
            "start_time", today_start.isoformat()
        ).lt("start_time", today_end.isoformat()).execute().count or 0
        
        # Leads por etapa
        leads_by_step = {}
        steps = ["start", "consent", "personal_data", "bant", "requirements", "meeting", "completed"]
        
        for step in steps:
            step_query = supabase.table("lead_qualification").select("id", count="exact").eq("current_step", step)
            if start_date:
                step_query = step_query.gte("created_at", start_date.isoformat())
            count = step_query.execute().count or 0
            leads_by_step[step] = count
        
        return {
            "total_users": total_users,
            "active_conversations": active_conversations,
            "meetings_today": meetings_today,
            "leads_by_step": leads_by_step,
            "total_leads": sum(leads_by_step.values())
        }
    
    def _get_conversion_funnel_data(self, date_range: str) -> List[Dict[str, Any]]:
        """Función auxiliar para obtener datos del funnel de conversión."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Calcular fechas según el rango
        now = datetime.now()
        if date_range == "week":
            start_date = now - timedelta(days=7)
        elif date_range == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = None
        
        # Obtener conteos por etapa
        query = supabase.table("lead_qualification").select("current_step", count="exact")
        if start_date:
            query = query.gte("created_at", start_date.isoformat())
        
        response = query.execute()
        
        # Procesar datos del funnel
        steps_order = ["start", "consent", "personal_data", "bant", "requirements", "meeting", "completed"]
        step_counts = {}
        
        # Contar por cada etapa
        for step in steps_order:
            step_query = supabase.table("lead_qualification").select("id", count="exact").eq("current_step", step)
            if start_date:
                step_query = step_query.gte("created_at", start_date.isoformat())
            count = step_query.execute().count or 0
            step_counts[step] = count
        
        # Calcular porcentajes de conversión
        total_leads = sum(step_counts.values())
        funnel_data = []
        
        for i, step in enumerate(steps_order):
            count = step_counts[step]
            percentage = (count / total_leads * 100) if total_leads > 0 else 0
            
            # Calcular conversión desde la etapa anterior
            conversion_rate = 0
            if i > 0:
                prev_step_count = step_counts[steps_order[i-1]]
                conversion_rate = (count / prev_step_count * 100) if prev_step_count > 0 else 0
            
            funnel_data.append({
                "step": step,
                "count": count,
                "percentage": round(percentage, 2),
                "conversion_rate": round(conversion_rate, 2)
            })
        
        return funnel_data
    
    def _get_activity_timeline(self, hours: int) -> List[Dict[str, Any]]:
        """Función auxiliar para obtener timeline de actividad."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Calcular fecha de inicio
        start_time = datetime.now() - timedelta(hours=hours)
        
        timeline = []
        
        # Nuevos usuarios
        users_response = supabase.table("users").select(
            "id, full_name, phone, created_at"
        ).gte("created_at", start_time.isoformat()).order("created_at", desc=True).execute()
        
        for user in users_response.data or []:
            timeline.append({
                "type": "new_user",
                "timestamp": user["created_at"],
                "data": {
                    "user_id": user["id"],
                    "full_name": user["full_name"],
                    "phone": user["phone"]
                }
            })
        
        # Nuevos mensajes
        messages_response = supabase.table("messages").select(
            "id, content, role, created_at, conversations(external_id, users(full_name))"
        ).gte("created_at", start_time.isoformat()).order("created_at", desc=True).limit(50).execute()
        
        for message in messages_response.data or []:
            timeline.append({
                "type": "new_message",
                "timestamp": message["created_at"],
                "data": {
                    "message_id": message["id"],
                    "content": message["content"][:100] + "..." if len(message["content"]) > 100 else message["content"],
                    "role": message["role"],
                    "user": message.get("conversations", {}).get("users", {}).get("full_name", "Usuario desconocido")
                }
            })
        
        # Nuevas meetings
        meetings_response = supabase.table("meetings").select(
            "id, subject, start_time, created_at, users(full_name)"
        ).gte("created_at", start_time.isoformat()).order("created_at", desc=True).execute()
        
        for meeting in meetings_response.data or []:
            timeline.append({
                "type": "new_meeting",
                "timestamp": meeting["created_at"],
                "data": {
                    "meeting_id": meeting["id"],
                    "subject": meeting["subject"],
                    "start_time": meeting["start_time"],
                    "user": meeting.get("users", {}).get("full_name", "Usuario desconocido")
                }
            })
        
        # Ordenar por timestamp descendente
        timeline.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return timeline[:100]  # Limitar a 100 eventos más recientes
    
    def _get_agent_performance_stats(self, date_range: str) -> Dict[str, Any]:
        """Función auxiliar para obtener estadísticas de performance del agente."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Calcular fechas según el rango
        now = datetime.now()
        if date_range == "week":
            start_date = now - timedelta(days=7)
        elif date_range == "month":
            start_date = now - timedelta(days=30)
        else:
            start_date = now - timedelta(days=7)  # Default a semana
        
        # Conversaciones con agente activado
        conv_with_agent = supabase.table("conversations").select("id", count="exact").eq(
            "agent_enabled", True
        ).gte("created_at", start_date.isoformat()).execute().count or 0
        
        # Conversaciones sin agente
        conv_without_agent = supabase.table("conversations").select("id", count="exact").eq(
            "agent_enabled", False
        ).gte("created_at", start_date.isoformat()).execute().count or 0
        
        # Promedio de mensajes por conversación con agente
        conv_with_agent_data = supabase.table("conversations").select(
            "id"
        ).eq("agent_enabled", True).gte("created_at", start_date.isoformat()).execute().data or []
        
        total_messages_with_agent = 0
        for conv in conv_with_agent_data:
            msg_count = supabase.table("messages").select("id", count="exact").eq(
                "conversation_id", conv["id"]
            ).execute().count or 0
            total_messages_with_agent += msg_count
        
        avg_messages_with_agent = (total_messages_with_agent / conv_with_agent) if conv_with_agent > 0 else 0
        
        # Promedio de mensajes por conversación sin agente
        conv_without_agent_data = supabase.table("conversations").select(
            "id"
        ).eq("agent_enabled", False).gte("created_at", start_date.isoformat()).execute().data or []
        
        total_messages_without_agent = 0
        for conv in conv_without_agent_data:
            msg_count = supabase.table("messages").select("id", count="exact").eq(
                "conversation_id", conv["id"]
            ).execute().count or 0
            total_messages_without_agent += msg_count
        
        avg_messages_without_agent = (total_messages_without_agent / conv_without_agent) if conv_without_agent > 0 else 0
        
        # Tasa de conversión a leads con/sin agente
        leads_with_agent = supabase.table("lead_qualification").select("id", count="exact").in_(
            "conversation_id", [c["id"] for c in conv_with_agent_data]
        ).execute().count or 0
        
        leads_without_agent = supabase.table("lead_qualification").select("id", count="exact").in_(
            "conversation_id", [c["id"] for c in conv_without_agent_data]
        ).execute().count or 0
        
        conversion_rate_with_agent = (leads_with_agent / conv_with_agent * 100) if conv_with_agent > 0 else 0
        conversion_rate_without_agent = (leads_without_agent / conv_without_agent * 100) if conv_without_agent > 0 else 0
        
        return {
            "conversations_with_agent": conv_with_agent,
            "conversations_without_agent": conv_without_agent,
            "avg_messages_with_agent": round(avg_messages_with_agent, 2),
            "avg_messages_without_agent": round(avg_messages_without_agent, 2),
            "leads_with_agent": leads_with_agent,
            "leads_without_agent": leads_without_agent,
            "conversion_rate_with_agent": round(conversion_rate_with_agent, 2),
            "conversion_rate_without_agent": round(conversion_rate_without_agent, 2),
            "agent_effectiveness": round(conversion_rate_with_agent - conversion_rate_without_agent, 2)
        }
    
    def _get_real_time_metrics(self) -> Dict[str, Any]:
        """Función auxiliar para obtener métricas en tiempo real."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Mensajes de la última hora
        one_hour_ago = datetime.now() - timedelta(hours=1)
        messages_last_hour = supabase.table("messages").select("id", count="exact").gte(
            "created_at", one_hour_ago.isoformat()
        ).execute().count or 0
        
        # Conversaciones activas (con mensajes en las últimas 2 horas)
        two_hours_ago = datetime.now() - timedelta(hours=2)
        active_conversations = supabase.table("conversations").select("id", count="exact").eq(
            "status", "active"
        ).execute().count or 0
        
        # Mensajes no leídos
        unread_messages = supabase.table("messages").select("id", count="exact").eq(
            "read", False
        ).eq("role", "user").execute().count or 0
        
        # Leads creados hoy
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        leads_today = supabase.table("lead_qualification").select("id", count="exact").gte(
            "created_at", today_start.isoformat()
        ).execute().count or 0
        
        # Meetings programadas para hoy
        today_end = today_start + timedelta(days=1)
        meetings_today = supabase.table("meetings").select("id", count="exact").gte(
            "start_time", today_start.isoformat()
        ).lt("start_time", today_end.isoformat()).execute().count or 0
        
        return {
            "messages_last_hour": messages_last_hour,
            "active_conversations": active_conversations,
            "unread_messages": unread_messages,
            "leads_today": leads_today,
            "meetings_today": meetings_today,
            "websocket_connections": self.connection_manager.get_connection_count() if hasattr(self.connection_manager, 'get_connection_count') else 0
        }
