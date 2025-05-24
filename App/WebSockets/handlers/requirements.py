"""
Handler para operaciones de requirements vía WebSocket.
"""

from typing import Dict, Any, List, Optional
import logging
from .base import BaseHandler
from ..events.dispatcher import dispatch_event
import asyncio
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)

class RequirementsHandler(BaseHandler):
    """Handler para operaciones de requirements."""
    
    def _register_actions(self) -> None:
        """Registra los manejadores de acciones para requirements."""
        self.action_handlers = {
            "get_requirements_by_lead": self.get_requirements_by_lead,
            "create_requirement_package": self.create_requirement_package,
            "update_requirements": self.update_requirements,
            "add_feature": self.add_feature,
            "add_integration": self.add_integration,
            "get_popular_features": self.get_popular_features,
            "get_popular_integrations": self.get_popular_integrations
        }
    
    # Función auxiliar para convertir funciones síncronas en asíncronas
    def to_async(self, func):
        @wraps(func)
        async def run(*args, **kwargs):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
        return run
    
    async def get_requirements_by_lead(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene requirements con features e integrations por lead."""
        lead_qualification_id = payload.get("lead_qualification_id")
        
        if not lead_qualification_id:
            raise ValueError("Se requiere lead_qualification_id")
        
        # Obtener requirements con JOINs
        requirements_data = await self.to_async(self._get_requirements_with_joins)(lead_qualification_id)
        
        return {
            "requirements": requirements_data
        }
    
    async def create_requirement_package(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Crea requirement + features[] + integrations[] en una transacción."""
        lead_qualification_id = payload.get("lead_qualification_id")
        requirement_data = payload.get("requirement")
        features = payload.get("features", [])
        integrations = payload.get("integrations", [])
        
        if not lead_qualification_id or not requirement_data:
            raise ValueError("Se requieren lead_qualification_id y requirement")
        
        # Crear paquete completo en transacción
        package_result = await self.to_async(self._create_requirement_package_transaction)(
            lead_qualification_id, requirement_data, features, integrations
        )
        
        # Notificar sobre la creación
        await dispatch_event("requirement_package_created", {
            "lead_qualification_id": lead_qualification_id,
            "requirement": package_result["requirement"],
            "features": package_result["features"],
            "integrations": package_result["integrations"]
        })
        
        return {
            "package": package_result
        }
    
    async def update_requirements(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Actualiza app_type y deadline de requirements."""
        requirement_id = payload.get("requirement_id")
        updates = payload.get("updates")
        
        if not requirement_id or not updates:
            raise ValueError("Se requieren requirement_id y updates")
        
        # Actualizar requirements
        updated_requirement = await self.to_async(self._update_requirement)(requirement_id, updates)
        
        # Notificar sobre la actualización
        await dispatch_event("requirement_updated", {
            "requirement_id": requirement_id,
            "requirement": updated_requirement
        })
        
        return {
            "requirement": updated_requirement
        }
    
    async def add_feature(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Añade una feature usando funciones de db_operations.py."""
        requirement_id = payload.get("requirement_id")
        feature_data = payload.get("feature")
        
        if not requirement_id or not feature_data:
            raise ValueError("Se requieren requirement_id y feature")
        
        # Usar función existente de db_operations.py
        from App.DB.db_operations import add_feature_to_requirement
        
        new_feature = await self.to_async(add_feature_to_requirement)(requirement_id, feature_data)
        
        # Notificar sobre la nueva feature
        await dispatch_event("feature_added", {
            "requirement_id": requirement_id,
            "feature": new_feature
        })
        
        return {
            "feature": new_feature
        }
    
    async def add_integration(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Añade una integration usando funciones de db_operations.py."""
        requirement_id = payload.get("requirement_id")
        integration_data = payload.get("integration")
        
        if not requirement_id or not integration_data:
            raise ValueError("Se requieren requirement_id y integration")
        
        # Usar función existente de db_operations.py
        from App.DB.db_operations import add_integration_to_requirement
        
        new_integration = await self.to_async(add_integration_to_requirement)(requirement_id, integration_data)
        
        # Notificar sobre la nueva integration
        await dispatch_event("integration_added", {
            "requirement_id": requirement_id,
            "integration": new_integration
        })
        
        return {
            "integration": new_integration
        }
    
    async def get_popular_features(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene features más populares ordenadas por uso."""
        limit = payload.get("limit", 20)
        
        # Obtener features populares
        popular_features = await self.to_async(self._get_popular_features_stats)(limit)
        
        return {
            "popular_features": popular_features,
            "limit": limit
        }
    
    async def get_popular_integrations(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Obtiene integrations más populares ordenadas por uso."""
        limit = payload.get("limit", 20)
        
        # Obtener integrations populares
        popular_integrations = await self.to_async(self._get_popular_integrations_stats)(limit)
        
        return {
            "popular_integrations": popular_integrations,
            "limit": limit
        }
    
    def _get_requirements_with_joins(self, lead_qualification_id: str) -> Optional[Dict]:
        """Función auxiliar para obtener requirements con JOINs."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Query con JOINs para obtener datos completos
        response = supabase.table("requirements").select("""
            *,
            features(*),
            integrations(*),
            lead_qualification(
                current_step,
                users(full_name, email, phone, company),
                conversations(external_id, platform)
            )
        """).eq("lead_qualification_id", lead_qualification_id).execute()
        
        if response.data:
            requirement = response.data[0]
            
            # Organizar datos para mejor estructura
            requirement["features_count"] = len(requirement.get("features", []))
            requirement["integrations_count"] = len(requirement.get("integrations", []))
            
            return requirement
        
        return None
    
    def _create_requirement_package_transaction(self, lead_qualification_id: str, 
                                              requirement_data: Dict[str, Any],
                                              features: List[Dict[str, Any]],
                                              integrations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Función auxiliar para crear paquete completo en transacción."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        try:
            # 1. Crear requirement
            requirement_insert_data = {
                "lead_qualification_id": lead_qualification_id,
                "app_type": requirement_data.get("app_type"),
                "deadline": requirement_data.get("deadline"),
                "created_at": datetime.now().isoformat()
            }
            
            requirement_response = supabase.table("requirements").insert(requirement_insert_data).execute()
            
            if not requirement_response.data:
                raise Exception("Error creando requirement")
            
            requirement = requirement_response.data[0]
            requirement_id = requirement["id"]
            
            # 2. Crear features
            created_features = []
            for feature_data in features:
                feature_insert_data = {
                    "requirement_id": requirement_id,
                    "name": feature_data.get("name"),
                    "description": feature_data.get("description"),
                    "created_at": datetime.now().isoformat()
                }
                
                feature_response = supabase.table("features").insert(feature_insert_data).execute()
                if feature_response.data:
                    created_features.append(feature_response.data[0])
            
            # 3. Crear integrations
            created_integrations = []
            for integration_data in integrations:
                integration_insert_data = {
                    "requirement_id": requirement_id,
                    "name": integration_data.get("name"),
                    "description": integration_data.get("description"),
                    "created_at": datetime.now().isoformat()
                }
                
                integration_response = supabase.table("integrations").insert(integration_insert_data).execute()
                if integration_response.data:
                    created_integrations.append(integration_response.data[0])
            
            return {
                "requirement": requirement,
                "features": created_features,
                "integrations": created_integrations,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error en transacción de requirement package: {str(e)}")
            return {
                "requirement": None,
                "features": [],
                "integrations": [],
                "success": False,
                "error": str(e)
            }
    
    def _update_requirement(self, requirement_id: str, updates: Dict[str, Any]) -> Dict:
        """Función auxiliar para actualizar requirement."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Preparar datos de actualización
        update_data = {
            **updates,
            "updated_at": datetime.now().isoformat()
        }
        
        # Filtrar solo campos permitidos
        allowed_fields = ["app_type", "deadline", "updated_at"]
        filtered_updates = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        response = supabase.table("requirements").update(filtered_updates).eq("id", requirement_id).execute()
        
        return response.data[0] if response.data else {}
    
    def _get_popular_features_stats(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Función auxiliar para obtener features populares."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Usar función RPC si existe, sino query manual
        try:
            # Intentar usar función RPC optimizada
            response = supabase.rpc('get_popular_features', {'limit_param': limit}).execute()
            
            if response.data:
                return response.data
        except:
            pass
        
        # Fallback: query manual con GROUP BY
        # Nota: Supabase no soporta GROUP BY directamente, así que hacemos una aproximación
        
        # Obtener todas las features
        all_features_response = supabase.table("features").select("name, description").execute()
        all_features = all_features_response.data if all_features_response.data else []
        
        # Contar manualmente cada feature
        feature_counts = {}
        for feature in all_features:
            name = feature["name"]
            if name in feature_counts:
                feature_counts[name]["count"] += 1
                # Mantener la descripción más reciente
                if feature.get("description"):
                    feature_counts[name]["description"] = feature["description"]
            else:
                feature_counts[name] = {
                    "name": name,
                    "description": feature.get("description", ""),
                    "count": 1
                }
        
        # Convertir a lista y ordenar por count
        popular_features = list(feature_counts.values())
        popular_features.sort(key=lambda x: x["count"], reverse=True)
        
        return popular_features[:limit]
    
    def _get_popular_integrations_stats(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Función auxiliar para obtener integrations populares."""
        from App.DB.supabase_client import get_supabase_client
        supabase = get_supabase_client()
        
        # Usar función RPC si existe, sino query manual
        try:
            # Intentar usar función RPC optimizada
            response = supabase.rpc('get_popular_integrations', {'limit_param': limit}).execute()
            
            if response.data:
                return response.data
        except:
            pass
        
        # Fallback: query manual con conteo
        
        # Obtener todas las integrations
        all_integrations_response = supabase.table("integrations").select("name, description").execute()
        all_integrations = all_integrations_response.data if all_integrations_response.data else []
        
        # Contar manualmente cada integration
        integration_counts = {}
        for integration in all_integrations:
            name = integration["name"]
            if name in integration_counts:
                integration_counts[name]["count"] += 1
                # Mantener la descripción más reciente
                if integration.get("description"):
                    integration_counts[name]["description"] = integration["description"]
            else:
                integration_counts[name] = {
                    "name": name,
                    "description": integration.get("description", ""),
                    "count": 1
                }
        
        # Convertir a lista y ordenar por count
        popular_integrations = list(integration_counts.values())
        popular_integrations.sort(key=lambda x: x["count"], reverse=True)
        
        return popular_integrations[:limit]
