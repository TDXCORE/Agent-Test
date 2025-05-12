import os
import sys
import logging
from fastapi import HTTPException

# Add parent directory to path to import supabase_client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supabase_client import get_supabase_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Dependency to get Supabase client
def get_supabase():
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=500, detail="Failed to connect to Supabase")
    return client
