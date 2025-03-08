import os
import json
import asyncio
import logging
import websockets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Generator

# Настройка логирования
logger = logging.getLogger(__name__)

# Получение OAuth токена из переменных окружения
BITQUERY_OAUTH_TOKEN = os.environ.get("BITQUERY_OAUTH_TOKEN")

# URL для GraphQL API и WebSocket
BITQUERY_API_URL = "https://streaming.bitquery.io/graphql"
BITQUERY_WS_URL = "wss://streaming.bitquery.io/graphql"

async def execute_query(query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Выполнить GraphQL запрос к Bitquery API
    
    Args:
        query: GraphQL запрос
        variables: Переменные для запроса
        
    Returns:
        Результат запроса в виде словаря
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BITQUERY_OAUTH_TOKEN}"
    }
    
    try:
        async with websockets.connect(BITQUERY_WS_URL, extra_headers=headers) as websocket:
            payload = {
                "query": query,
                "variables": variables or {}
            }
            
            logger.debug(f"Sending query to Bitquery: {payload}")
            await websocket.send(json.dumps(payload))
            
            response = await websocket.recv()
            result = json.loads(response)
            
            if "errors" in result:
                logger.error(f"GraphQL errors: {result['errors']}")
                
            return result
    except Exception as e:
        logger.error(f"Error executing Bitquery query: {str(e)}")
        logger.debug(f"Failed query: {query}")
        logger.debug(f"Variables: {variables}")
        return {"errors": [{"message": str(e)}]}

async def fetch_token_metrics(token_address: str) -> Dict[str, float]:
    """
    Получить текущие метрики для токена
    
    Args:
        token_address: Адрес токена (mint address)
        
    Returns:
        Словарь с метриками токена (цена, рыночная капитализация, объем за 24ч)
    """
    logger.info(f"Fetching metrics for token: {token_address}")
    
    query = """
    query($token: String!, $timeAgo: ISO8601DateTime!) {
      Solana {
        # Get latest price
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
              Amount
            }
            Sell {
              Amount
            }
            Dex {
              ProtocolName
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
            volumeUSD: sum(of: Buy_AmountInUSD)
          }
        }
        
        # Get token supply
        TokenBalances(
          where: {
            Currency: {
              MintAddress: {is: $token}
            }
          }
        ) {
          totalSupply: sum(of: Balance_Amount)
        }
      }
    }
    """
    
    # Рассчитываем время 24 часа назад в ISO формате
    time_ago = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    
    variables = {
        "token": token_address,
        "timeAgo": time_ago
    }
    
    result = await execute_query(query, variables)
    
    if not result or "data" not in result or "errors" in result:
        logger.warning(f"Failed to fetch metrics for token {token_address}")
        return {}
    
    data = result["data"]["Solana"]
    
    # Извлекаем цену из последней сделки
    price = 0
    if data["DEXTrades"] and len(data["DEXTrades"]) > 0:
        price = float(data["DEXTrades"][0]["Trade"]["Buy"]["Price"] or 0)
    
    # Получаем общее предложение токенов
    total_supply = 1000000000  # Значение по умолчанию
    if data["TokenBalances"] and data["TokenBalances"]["totalSupply"]:
        total_supply = float(data["TokenBalances"]["totalSupply"])
    
    # Рассчитываем рыночную капитализацию
    market_cap = price * total_supply
    
    # Извлекаем объем за 24 часа
    volume_24h = 0
    volume_usd_24h = 0
    if len(data["DEXTrades"]) > 1:
        volume_24h = float(data["DEXTrades"][1]["Trade"]["volume"] or 0)
        volume_usd_24h = float(data["DEXTrades"][1]["Trade"]["volumeUSD"] or 0)
    
    logger.info(f"Metrics for {token_address}: price={price}, market_cap={market_cap}, volume_24h={volume_24h}")
    
    return {
        "price": price,
        "market_cap": market_cap,
        "volume_24h": volume_24h,
        "volume_usd_24h": volume_usd_24h,
        "total_supply": total_supply,
        "last_updated": datetime.utcnow().isoformat()
    }

async def check_raydium_migration(token_address: str) -> Dict[str, Any]:
    """
    Проверить, мигрировал ли токен на Raydium
    
    Args:
        token_address: Адрес токена
        
    Returns:
        Словарь с информацией о миграции
    """
    logger.info(f"Checking Raydium migration for token: {token_address}")
    
    query = """
    query($token: String!) {
      Solana {
        DEXTrades(
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
          orderBy: {descending: Block_Time}
        ) {
          count
          Block {
            Time
          }
        }
      }
    }
    """
    
    variables = {
        "token": token_address
    }
    
    result = await execute_query(query, variables)
    
    if not result or "data" not in result or "errors" in result:
        logger.warning(f"Failed to check Raydium migration for token {token_address}")
        return {"migrated": False}
    
    data = result["data"]["Solana"]["DEXTrades"]
    
    migrated = data and data["count"] > 0
    migration_time = None
    
    if migrated and data["Block"] and data["Block"]["Time"]:
        migration_time = data["Block"]["Time"]
    
    logger.info(f"Raydium migration for {token_address}: migrated={migrated}, time={migration_time}")
    
    return {
        "migrated": migrated,
        "migration_time": migration_time
    }

async def calculate_bonding_curve(token_address: str) -> Dict[str, Any]:
    """
    Рассчитать прогресс кривой связывания для токена
    
    Args:
        token_address: Адрес токена
        
    Returns:
        Словарь с информацией о прогрессе кривой связывания
    """
    logger.info(f"Calculating bonding curve for token: {token_address}")
    
    query = """
    query($token: String!) {
      Solana {
        TokenBalances(
          where: {
            Currency: {
              MintAddress: {is: $token}
            }
          }
        ) {
          BalanceUpdate {
            Amount
          }
          Currency {
            TotalSupply
          }
          Balance {
            sum: sum(of: Amount)
          }
          holderCount: count(distinct: Balance_Address)
        }
      }
    }
    """
    
    variables = {
        "token": token_address
    }
    
    result = await execute_query(query, variables)
    
    if not result or "data" not in result or "errors" in result:
        logger.warning(f"Failed to calculate bonding curve for token {token_address}")
        return {"progress": 0}
    
    # Рассчитываем прогресс кривой связывания
    # Формула: BondingCurveProgress = 100 - ((leftTokens*100)/(initialRealTokenReserves))
    total_supply = 1000000000  # Значение по умолчанию
    reserved_tokens = 206900000  # Зарезервированные токены
    initial_real_token_reserves = total_supply - reserved_tokens
    
    data = result["data"]["Solana"]["TokenBalances"]
    
    # Получаем общее предложение из запроса, если доступно
    if data and data["Currency"] and data["Currency"]["TotalSupply"]:
        total_supply = float(data["Currency"]["TotalSupply"])
    
    # Рассчитываем оставшиеся токены
    left_tokens = initial_real_token_reserves  # Значение по умолчанию
    
    if data and data["Balance"] and data["Balance"]["sum"]:
        circulating = float(data["Balance"]["sum"])
        left_tokens = initial_real_token_reserves - circulating
    
    # Рассчитываем прогресс
    if left_tokens <= 0:
        progress = 100.0
    else:
        progress = 100 - ((left_tokens * 100) / initial_real_token_reserves)
        progress = max(0, min(100, progress))  # Убеждаемся, что значение между 0-100
    
    holder_count = data["holderCount"] if data and data["holderCount"] else 0
    
    logger.info(f"Bonding curve for {token_address}: progress={progress}%, holders={holder_count}")
    
    return {
        "progress": progress,
        "left_tokens": left_tokens,
        "total_supply": total_supply,
        "holder_count": holder_count
    }

async def monitor_new_tokens() -> Generator[Dict[str, Any], None, None]:
    """
    Подписаться на события создания новых токенов
    
    Yields:
        Информация о новом токене
    """
    logger.info("Starting monitoring for new token creation events")
    
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
            Fee
            Status
          }
          Block {
            Time
            Height
          }
        }
      }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BITQUERY_OAUTH_TOKEN}"
    }
    
    reconnect_delay = 5  # Начальная задержка перед повторным подключением (в секундах)
    
    while True:
        try:
            logger.info("Connecting to Bitquery WebSocket for token monitoring")
            async with websockets.connect(BITQUERY_WS_URL, extra_headers=headers) as websocket:
                await websocket.send(json.dumps({"query": subscription}))
                logger.info("Subscription started for new token monitoring")
                
                # Сбрасываем задержку после успешного подключения
                reconnect_delay = 5
                
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    # Обрабатываем новое создание токена
                    if "data" in data and data["data"]["Solana"]["TokenTransfers"]:
                        transfer = data["data"]["Solana"]["TokenTransfers"][0]
                        
                        # Проверяем, является ли это транзакцией создания токена
                        # Здесь нужна дополнительная логика для определения создания токена
                        
                        logger.info(f"Detected potential new token: {transfer['Transaction']['Hash']}")
                        yield {
                            "transaction_hash": transfer["Transaction"]["Hash"],
                            "block_time": transfer["Block"]["Time"],
                            "block_height": transfer["Block"]["Height"],
                            "sender": transfer["Transfer"]["Sender"]["Address"],
                            "receiver": transfer["Transfer"]["Receiver"]["Address"],
                            "amount": transfer["Transfer"]["Amount"],
                            "detected_at": datetime.utcnow().isoformat()
                        }
        except Exception as e:
            logger.error(f"Error in token monitoring: {str(e)}")
            
            # Экспоненциальное увеличение задержки при повторных ошибках (до 60 секунд)
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, 60)

async def get_token_holders(token_address: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Получить список держателей токена
    
    Args:
        token_address: Адрес токена
        limit: Максимальное количество держателей для возврата
        
    Returns:
        Список держателей токена с их балансами
    """
    logger.info(f"Fetching holders for token: {token_address}")
    
    query = """
    query($token: String!, $limit: Int!) {
      Solana {
        TokenBalances(
          where: {
            Currency: {
              MintAddress: {is: $token}
            }
          }
          limit: {count: $limit}
          orderBy: {descending: Balance_Amount}
        ) {
          Balance {
            Address
            Amount
          }
        }
      }
    }
    """
    
    variables = {
        "token": token_address,
        "limit": limit
    }
    
    result = await execute_query(query, variables)
    
    if not result or "data" not in result or "errors" in result:
        logger.warning(f"Failed to fetch holders for token {token_address}")
        return []
    
    holders = []
    data = result["data"]["
