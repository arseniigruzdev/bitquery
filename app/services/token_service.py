from datetime import datetime, timedelta
import logging
from ..database import get_supabase
from .bitquery_service import fetch_token_metrics, check_raydium_migration, calculate_bonding_curve
from .developer_service import update_developer_stats

supabase = get_supabase()
logger = logging.getLogger(__name__)

async def get_tokens(limit=100, offset=0, sort_by="market_cap", descending=True):
    """Get tokens with pagination and sorting"""
    try:
        valid_sort_fields = ["market_cap", "price", "volume_24h", "creation_time", 
                            "bonding_curve_progress", "king_of_hill_time", "raydium_migration_time"]
        
        if sort_by not in valid_sort_fields:
            sort_by = "market_cap"
        
        order_direction = "desc" if descending else "asc"
        
        result = supabase.table("tokens").select("*").order(sort_by, order_direction).range(offset, offset + limit - 1).execute()
        return result.data
    except Exception as e:
        logger.error(f"Error getting tokens: {str(e)}")
        raise

async def get_token_by_address(token_address):
    """Get a token by its address"""
    try:
        result = supabase.table("tokens").select("*").eq("token_address", token_address).execute()
        
        if not result.data:
            return None
        
        return result.data[0]
    except Exception as e:
        logger.error(f"Error getting token by address {token_address}: {str(e)}")
        raise

async def create_token(token_data):
    """Create a new token record"""
    try:
        # Add current timestamp
        token_data["last_updated"] = datetime.utcnow().isoformat()
        token_data["creation_time"] = token_data.get("creation_time", datetime.utcnow().isoformat())
        
        # Insert token data
        result = supabase.table("tokens").insert(token_data).execute()
        
        # Update developer stats
        await update_developer_stats(token_data["creator_address"])
        
        # Return the created token
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error creating token: {str(e)}")
        raise

async def update_token(token_address, token_data):
    """Update an existing token record"""
    try:
        # Add current timestamp for last_updated
        token_data["last_updated"] = datetime.utcnow().isoformat()
        
        # Update token data
        result = supabase.table("tokens").update(token_data).eq("token_address", token_address).execute()
        
        return result.data[0] if result.data else None
    except Exception as e:
        logger.error(f"Error updating token {token_address}: {str(e)}")
        raise

async def refresh_token_metrics(token_address):
    """Refresh token metrics from Bitquery"""
    try:
        # Get current token data
        token = await get_token_by_address(token_address)
        if not token:
            logger.error(f"Token {token_address} not found")
            return None
        
        # Fetch updated metrics from Bitquery
        metrics = await fetch_token_metrics(token_address)
        
        # Check Raydium migration status
        raydium_status = await check_raydium_migration(token_address)
        
        # Calculate bonding curve progress
        bonding_curve = await calculate_bonding_curve(token_address)
        
        # Prepare update data
        update_data = {
            "price": metrics.get("price"),
            "volume_24h": metrics.get("volume_24h"),
            "market_cap": metrics.get("market_cap"),
            "bonding_curve_progress": bonding_curve.get("progress"),
            "raydium_migration_time": raydium_status.get("migration_time"),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Filter out None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        # Update token
        return await update_token(token_address, update_data)
    except Exception as e:
        logger.error(f"Error refreshing token metrics for {token_address}: {str(e)}")
        raise

async def get_trending_tokens(limit=10):
    """Get trending tokens based on 24h volume growth"""
    try:
        # Get tokens with highest 24h volume
        result = supabase.table("tokens").select("*").order("volume_24h", "desc").limit(limit).execute()
        return result.data
    except Exception as e:
        logger.error(f"Error getting trending tokens: {str(e)}")
        raise

async def delete_token(token_address):
    """Delete a token by its address"""
    try:
        result = supabase.table("tokens").delete().eq("token_address", token_address).execute()
        return result.data
    except Exception as e:
        logger.error(f"Error deleting token {token_address}: {str(e)}")
        raise

async def search_tokens(query, limit=20):
    """Search tokens by name or symbol"""
    try:
        # Search by name or symbol using ilike (case-insensitive)
        result = supabase.table("tokens").select("*").or_(
            f"name.ilike.%{query}%,symbol.ilike.%{query}%"
        ).limit(limit).execute()
        return result.data
    except Exception as e:
        logger.error(f"Error searching tokens with query '{query}': {str(e)}")
        raise

async def get_token_history(token_address, days=30):
    """Get historical data for a token"""
    try:
        # Calculate the date from which to fetch history
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Get historical data
        result = supabase.table("token_history").select("*").eq(
            "token_address", token_address
        ).gte("timestamp", start_date).order("timestamp", "asc").execute()
        
        return result.data
    except Exception as e:
        logger.error(f"Error getting history for token {token_address}: {str(e)}")
        raise

async def batch_update_tokens(token_addresses):
    """Update metrics for multiple tokens in batch"""
    try:
        results = []
        for address in token_addresses:
            result = await refresh_token_metrics(address)
            results.append({"address": address, "updated": result is not None})
        return results
    except Exception as e:
        logger.error(f"Error in batch update of tokens: {str(e)}")
        raise

async def get_tokens_by_creator(creator_address, limit=50, offset=0):
    """Get tokens created by a specific address"""
    try:
        result = supabase.table("tokens").select("*").eq(
            "creator_address", creator_address
        ).order("creation_time", "desc").range(offset, offset + limit - 1).execute()
        
        return result.data
    except Exception as e:
        logger.error(f"Error getting tokens by creator {creator_address}: {str(e)}")
        raise
