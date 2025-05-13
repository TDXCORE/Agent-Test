"""
Common dependencies for the application.
This module contains functions that can be used as dependencies in FastAPI routes.
"""
import logging
from App.DB.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

def get_supabase():
    """
    Dependency to get the Supabase client.
    This function can be used as a dependency in FastAPI routes.
    
    Returns:
        Supabase client instance
    """
    logger.debug("Getting Supabase client from dependency")
    return get_supabase_client()
