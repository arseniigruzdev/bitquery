import asyncio
import os
import json
from datetime import datetime, timedelta
import websockets
from supabase import create_client

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Bitquery configuration
BITQUERY_API_KEY = os.environ.get("BITQUERY_API_KEY")

async def monitor_new_tokens():
    """Subscribe to new token creation events"""
    subscription = """
    subscription {
      Solana {
        TokenTransfers(
          where: {
            Transfer: {
              Currency: {
                MintAddress: {is: "So11111111111111111111111111111111111111112"}
              }
            }
          }
        ) {
          Transfer {
            Amount
            Receiver {
              Address
            }
            Sender {
              Address
            }
            Currency {
              MintAddress
              Name
              Symbol
            }
          }
          Transaction {
            Hash
          }
          Block {
            Time
          }
        }
      }
    }
    """
    
    headers = {
        "Content-Type": "
