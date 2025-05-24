"""
Handler para operaciones de leads vía WebSocket.
"""

from typing import Dict, Any, List, Optional
import logging
from .base import BaseHandler
from ..events.dispatcher import dispatch_event
import asyncio
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LeadsHandler(BaseHandler):
    """Handler para operaciones de leads."""
    
    def _register_actions(self) -> None:
        """Registra los manejadores de acciones para leads."""
        self.action_handlers = {
            "get_all_leads": self.get_all_leads,
            "get_lead_pipeline": self.get_lead_pipeline,
            "get_lead_with_complete_data": self.get_lead_with_complete_data,
            "update_lead_step": self.update_lead_step,
            "get_conversion_stats": self.get_conversion_stats,
            "get_abandoned_leads": self.get_abandoned_leads
        }
    
    # Función auxiliar para convertir funciones síncronas en asíncronas
    def to_async(self, func):
        @wraps(func)
        async def run(*args, **kwargs):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        return run
    
    async def get_all_leads(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene todos los leads con datos completos."""
        limit = payload.get("limit", 50)
        offset = payload.get("offset", 0)
        current_step = payload.get("current_step")
        
        # Obtener leads con JOINs
        leads = await self.to_async(self._get_all_leads_with_joins)(limit, offset, current_step)
        
        return {
            "leads": leads,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(leads)
            }
        }
    
    async def get_lead_pipeline(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene el pipeline de leads agrupado por etapa."""
        date_range = payload.get("date_range", "all")
        
        # Obtener pipeline de leads
        pipeline = await self.to_async(self._get_lead_pipeline_data)(date_range)
        
        return {
            "pipeline": pipeline,
            "date_range": date_range,
            "generated_at": datetime.now().isoformat()
        }
    
    async def get_lead_with_complete_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene un lead con todo su ecosistema de datos."""
        lead_id = payload.get("lead_id")
        user_id = payload.get("user_id")
        conversation_id = payload.get("conversation_id")
        
        if not lead_id and not user_id and not conversation_id:
            raise ValueError("Se requiere lead_id, user_id o conversation_id")
        
        # Obtener lead completo
        lead_data = await self.to_async(self._get_complete_lead_data)(lead_id, user_id, conversation_id)
        
        if not lead_data:
            raise ValueError("Lead no encontrado")
        
        return {
            "lead": lead_data
        }
    
    async def update_lead_step(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza manualmente el current_step de un lead."""
        lead_id = payload.get("lead_id")
        new_step = payload.get("new_step") or payload.get("current_step")
        
        if not lead_id or not new_step:
            raise ValueError("Se requieren lead_id y current_step")
        
        # Validar que el step sea válido
        valid_steps = ["start", "consent", "personal_data", "bant", "requirements", "meeting", "completed"]
        if new_step not in valid_steps:
            raise ValueError(f"Step inválido. Debe ser uno de: {', '.join(valid_steps)}")
        
        # Actualizar step
        updated_lead = await self.to_async(self._update_lead_step)(lead_id, new_step)
        
        # Notificar sobre la actualización
        await dispatch_event("lead_step_updated", {
            "lead_id": lead_id,
            "new_step": new_step,
            "lead": updated_lead
        })
        
        return {
            "lead": updated_lead,
            "previous_step": updated_lead.get("previous_step"),
            "current_step": new_step
        }
    
    async def get_conversion_stats(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene estadísticas de conversión entre etapas."""
        date_range = payload.get("date_range", "all")
        
        # Obtener estadísticas de conversión
        stats = await self.to_async(self._get_conversion_statistics)(date_range)
        
        return {
            "conversion_stats": stats,
            "date_range": date_range,
            "generated_at": datetime.now().isoformat()
        }
    
    async def get_abandoned_leads(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene leads abandonados (no completados en más de 7 días)."""
        days_threshold = payload.get("days_threshold", 7)
        limit = payload.get("limit", 50)
        offset = payload.get("offset", 0)
        
        # Obtener leads abandonados
        abandoned_leads = await self.to_async(self._get_abandoned_leads)(days_threshold, limit, offset)
        
        return {
            "abandoned_leads": abandoned_leads,
            "days_threshold": days_threshold,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": len(abandoned_leads)
            }
        }
    
    def _get_all_leads_with_joins(self, limit: int = 50, offset: int = 0, current_step: Optional[str] = None) -> List[Dict]:
        """Función auxiliar para obtener leads con JOINs."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Query con JOINs para obtener datos completos
        query = supabase.table("lead_qualification").select("""
            *,
            users(id, full_name, email, phone, company),
            conversations(id, external_id, platform, status, agent_enabled),
            bant_data(*),
            requirements(*, features(*), integrations(*)),
            meetings(id, subject, start_time, end_time, status, online_meeting_url)
        """)
        
        if current_step:
            query = query.eq("current_step", current_step)
        
        response = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
        
        return response.data if response.data else []
    
    def _get_lead_pipeline_data(self, date_range: str) -> List[Dict[str, Any]]:
        """Función auxiliar para obtener datos del pipeline."""
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
        steps = ["start", "consent", "personal_data", "bant", "requirements", "meeting", "completed"]
        pipeline_data = []
        
        for step in steps:
            query = supabase.table("lead_qualification").select("id", count="exact").eq("current_step", step)
            if start_date:
                query = query.gte("created_at", start_date.isoformat())
            
            count = query.execute().count or 0
            
            # Obtener algunos leads de ejemplo para esta etapa
            examples_query = supabase.table("lead_qualification").select("""
                id, created_at, updated_at,
                users(full_name, phone, email),
                conversations(external_id, platform)
            """).eq("current_step", step)
            
            if start_date:
                examples_query = examples_query.gte("created_at", start_date.isoformat())
            
            examples = examples_query.order("updated_at", desc=True).limit(5).execute().data or []
            
            pipeline_data.append({
                "step": step,
                "count": count,
                "examples": examples
            })
        
        return pipeline_data
    
    def _get_complete_lead_data(self, lead_id: Optional[str] = None, user_id: Optional[str] = None, 
                               conversation_id: Optional[str] = None) -> Optional[Dict]:
        """Función auxiliar para obtener datos completos de un lead."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Construir query base
        query = supabase.table("lead_qualification").select("""
            *,
            users(id, full_name, email, phone, company, created_at),
            conversations(id, external_id, platform, status, agent_enabled, created_at, updated_at),
            bant_data(*),
            requirements(*, features(*), integrations(*)),
            meetings(*)
        """)
        
        # Aplicar filtros
        if lead_id:
            query = query.eq("id", lead_id)
        elif user_id:
            query = query.eq("user_id", user_id)
        elif conversation_id:
            query = query.eq("conversation_id", conversation_id)
        
        response = query.execute()
        
        if not response.data:
            return None
        
        lead = response.data[0]
        
        # Obtener mensajes de la conversación
        if lead.get("conversations"):
            conv_id = lead["conversations"]["id"]
            messages_response = supabase.table("messages").select(
                "id, content, role, message_type, created_at, read"
            ).eq("conversation_id", conv_id).order("created_at", desc=True).limit(20).execute()
            
            lead["conversations"]["recent_messages"] = messages_response.data if messages_response.data else []
        
        return lead
    
    def _update_lead_step(self, lead_id: str, new_step: str) -> Dict:
        """Función auxiliar para actualizar el step de un lead."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Obtener lead actual para guardar el step anterior
        current_lead = supabase.table("lead_qualification").select("current_step").eq("id", lead_id).execute()
        previous_step = current_lead.data[0]["current_step"] if current_lead.data else None
        
        # Actualizar step
        update_data = {
            "current_step": new_step,
            "updated_at": datetime.now().isoformat()
        }
        
        response = supabase.table("lead_qualification").update(update_data).eq("id", lead_id).execute()
        
        if response.data:
            updated_lead = response.data[0]
            updated_lead["previous_step"] = previous_step
            return updated_lead
        
        return {}
    
    def _get_conversion_statistics(self, date_range: str) -> Dict[str, Any]:
        """Función auxiliar para obtener estadísticas de conversión."""
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
        steps = ["start", "consent", "personal_data", "bant", "requirements", "meeting", "completed"]
        step_counts = {}
        
        for step in steps:
            query = supabase.table("lead_qualification").select("id", count="exact").eq("current_step", step)
            if start_date:
                query = query.gte("created_at", start_date.isoformat())
            count = query.execute().count or 0
            step_counts[step] = count
        
        # Calcular estadísticas de conversión
        total_leads = sum(step_counts.values())
        conversion_stats = []
        
        for i, step in enumerate(steps):
            count = step_counts[step]
            
            # Porcentaje del total
            percentage_of_total = (count / total_leads * 100) if total_leads > 0 else 0
            
            # Tasa de conversión desde la etapa anterior
            conversion_rate = 0
            if i > 0:
                prev_step_count = step_counts[steps[i-1]]
                conversion_rate = (count / prev_step_count * 100) if prev_step_count > 0 else 0
            
            # Tasa de abandono (leads que no pasaron a la siguiente etapa)
            abandonment_rate = 0
            if i < len(steps) - 1:
                next_step_count = step_counts[steps[i+1]]
                abandonment_rate = ((count - next_step_count) / count * 100) if count > 0 else 0
            
            conversion_stats.append({
                "step": step,
                "count": count,
                "percentage_of_total": round(percentage_of_total, 2),
                "conversion_rate": round(conversion_rate, 2),
                "abandonment_rate": round(abandonment_rate, 2)
            })
        
        # Calcular métricas generales
        completed_leads = step_counts.get("completed", 0)
        overall_conversion_rate = (completed_leads / total_leads * 100) if total_leads > 0 else 0
        
        return {
            "step_stats": conversion_stats,
            "overall_stats": {
                "total_leads": total_leads,
                "completed_leads": completed_leads,
                "overall_conversion_rate": round(overall_conversion_rate, 2)
            }
        }
    
    def _get_abandoned_leads(self, days_threshold: int = 7, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Función auxiliar para obtener leads abandonados."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Calcular fecha límite
        threshold_date = datetime.now() - timedelta(days=days_threshold)
        
        # Obtener leads no completados y antiguos
        response = supabase.table("lead_qualification").select("""
            *,
            users(full_name, email, phone, company),
            conversations(external_id, platform, status),
            bant_data(budget, authority, need, timeline),
            requirements(app_type, deadline)
        """).neq("current_step", "completed").lt(
            "updated_at", threshold_date.isoformat()
        ).order("updated_at", desc=True).range(offset, offset + limit - 1).execute()
        
        abandoned_leads = response.data if response.data else []
        
        # Calcular días desde la última actualización
        for lead in abandoned_leads:
            if lead.get("updated_at"):
                updated_at = datetime.fromisoformat(lead["updated_at"].replace('Z', '+00:00'))
                days_since_update = (datetime.now() - updated_at.replace(tzinfo=None)).days
                lead["days_since_update"] = days_since_update
        
        return abandoned_leads
