from datetime import datetime, timedelta
from ..database import get_supabase
from .bitquery_service import fetch_token_metrics, check_raydium_migration, calculate_bonding_curve
from .developer_service import update_developer_stats

supabase = get_supabase()

async def get_tokens(limit=100, offset=0, sort_by="market_cap", descending=True):
    """Get tokens with pagination and sorting"""
    valid_sort_fields = ["market_cap", "price", "volume_24h", "creation_time", 
                         "bonding_curve_progress", "king_of_hill_time", "raydium_migration_time"]
    
    if sort_by not in valid_sort_fields:
        sort_by = "market_cap"
    
    order_direction = "desc" if descending else "asc"
    
    result = supabase.table("tokens").select("*").order(sort_by, order_direction).range(offset, offset + limit - 1).execute()
    return result.data

async def get_token_by_address(token_address):
    """Get a token by its address"""
    result = supabase.table("tokens").select("*").eq("token_address", token_address).execute()
    
    if not result.data:
        return None
    
    return result.data[0]

async def create_token(token_data):
    """Create a new token record"""
    token_data["last_updated"] = datetime.utcnow().isoformat()
    
    result = supabase.table("tokens").insert(token_data).execute()
    
    # Update developer stats
    await update_developer_stats(token_data["creator_address"])
