import os
import json
import asyncio
import websockets
from datetime import datetime

BITQUERY_API_KEY = os.environ.get("BITQUERY_API_KEY")

async def execute_query(query, variables=None):
    """Execute a GraphQL query against Bitquery API"""
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": BITQUERY_API_KEY
    }
    
    try:
        async with websockets.connect("wss://streaming.bitquery.io/graphql", extra_headers=headers) as websocket:
            await websocket.send(json.dumps({
                "query": query,
                "variables": variables or {}
            }))
            
            response = await websocket.recv()
            return json.loads(response)
    except Exception as e:
        print(f"Error executing Bitquery query: {str(e)}")
        return None

async def fetch_token_metrics(token_address):
    """Fetch current metrics for a token"""
    query = """
    query($token: String!) {
      Solana {
        DEXTrades(
          where: {
            Trade: {
              Currency: {
                MintAddress: {is: $token}
              }
            }
          }
          limit: {count: 1}
          orderBy: {descending: Block_Time}
        ) {
          Trade {
            Buy {
              Price
            }
          }
          Block {
            Time
          }
        }
        
        # Get 24h volume
        DEXTrades(
          where: {
            Trade: {
              Currency: {
                MintAddress: {is: $token}
              }
            }
            Block: {
              Time: {gt: $timeAgo}
            }
          }
        ) {
          tradeAmount: count
          Trade {
            volume: sum(of: Buy_Amount)
          }
        }
      }
    }
    """
    
    # Calculate 24 hours ago
    time_ago = (datetime.utcnow().timestamp() - 86400)
    
    variables = {
        "token": token_address,
        "timeAgo": time_ago
    }
    
    result = await execute_query(query, variables)
    
    if not result or "data" not in result:
        return {}
    
    data = result["data"]["Solana"]
    
    # Extract price from latest trade
    price = 0
    if data["DEXTrades"] and len(data["DEXTrades"]) > 0:
        price = float(data["DEXTrades"][0]["Trade"]["Buy"]["Price"])
    
    # Calculate market cap (1 billion supply)
    market_cap = price * 1000000000
    
    # Extract 24h volume
    volume_24h = 0
    if len(data["DEXTrades"]) > 1:
        volume_24h = float(data["DEXTrades"][1]["Trade"]["volume"])
    
    return {
        "price": price,
        "market_cap": market_cap,
        "volume_24h": volume_24h
    }

async def check_raydium_migration(token_address):
    """Check if a token has migrated to Raydium"""
    query = """
    query($token: String!) {
      Solana {
        DEXTradeByTokens(
          where: {
            Trade: {
              Currency: {
                MintAddress: {is: $token}
              },
              Dex: {
                ProtocolName: {is: "raydium"}
              }
            }
          }
          limit: {count: 1}
        ) {
          count
        }
      }
    }
    """
    
    variables = {
        "token": token_address
    }
    
    result = await execute_query(query, variables)
    
    if not result or "data" not in result:
        return False
    
    trade_count = result["data"]["Solana"]["DEXTradeByTokens"]["count"]
    return trade_count > 0

async def calculate_bonding_curve(token_address):
    """Calculate bonding curve progress for a token"""
    query = """
    query($token: String!) {
      Solana {
        BalanceUpdates(
          where: {
            BalanceUpdate: {
              Currency: {
                MintAddress: {is: $token}
              }
            }
          }
        ) {
          BalanceUpdate {
            Amount
          }
        }
      }
    }
    """
    
    variables = {
        "token": token_address
    }
    
    result = await execute_query(query, variables)
    
    if not result or "data" not in result:
        return 0
    
    # Calculate bonding curve progress
    # Formula: BondingCurveProgress = 100 - ((leftTokens*100)/(initialRealTokenReserves))
    total_supply = 1000000000
    reserved_tokens = 206900000
    initial_real_token_reserves = total_supply - reserved_tokens
    
    # Calculate left tokens (simplified)
    left_tokens = initial_real_token_reserves  # Default
    
    if "data" in result and result["data"]["Solana"]["BalanceUpdates"]:
        # Sum up all balance updates to get circulating supply
        circulating = sum([float(update["BalanceUpdate"]["Amount"]) for update in result["data"]["Solana"]["BalanceUpdates"]])
        left_tokens = initial_real_token_reserves - circulating
    
    # Calculate progress
    if left_tokens <= 0:
        return 100.0
    
    progress = 100 - ((left_tokens * 100) / initial_real_token_reserves)
    return max(0, min(100, progress))  # Ensure between 0-100

async def monitor_new_tokens():
    """Subscribe to new token creation events"""
    subscription = """
    subscription {
      Solana {
        TokenTransfers(
          where: {
            Transfer: {
              Currency: {
                MintAddress: {is: "11111111111111111111111111111111"}
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
        "Content-Type": "application/json",
        "X-API-KEY": BITQUERY_API_KEY
    }
    
    async with websockets.connect("wss://streaming.bitquery.io/graphql", extra_headers=headers) as websocket:
        await websocket.send(json.dumps({"query": subscription}))
        
        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)
                
                # Process new token creation
                if "data" in data and data["data"]["Solana"]["TokenTransfers"]:
                    # Logic to detect and process new token creation
                    # This is a simplified version - you'll need to enhance this
                    transfer = data["data"]["Solana"]["TokenTransfers"][0]
                    
                    # Check if this is a token creation transaction
                    # Add your logic here
                    
                    yield transfer
            except Exception as e:
                print(f"Error in token monitoring: {str(e)}")
                await asyncio.sleep(5)  # Wait before reconnecting
