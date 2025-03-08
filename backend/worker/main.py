import asyncio
import os
import json
from datetime import datetime
import websockets
from supabase import create_client
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("solana_token_monitor")

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
        "Content-Type": "application/json",
        "X-API-KEY": BITQUERY_API_KEY
    }
    
    url = "wss://streaming.bitquery.io/graphql"
    
    while True:
        try:
            logger.info("Connecting to Bitquery WebSocket...")
            async with websockets.connect(url, extra_headers=headers, subprotocols=["graphql-ws"]) as websocket:
                # Инициализация соединения
                await websocket.send(json.dumps({"type": "connection_init"}))
                
                # Ожидаем подтверждение соединения
                response = await websocket.recv()
                response_data = json.loads(response)
                
                if response_data.get("type") == "connection_ack":
                    logger.info("Connection acknowledged")
                    
                    # Отправляем запрос на подписку
                    await websocket.send(json.dumps({
                        "type": "start",
                        "id": "1",
                        "payload": {
                            "query": subscription
                        }
                    }))
                    
                    # Обрабатываем входящие сообщения
                    while True:
                        response = await websocket.recv()
                        data = json.loads(response)
                        
                        if data.get("type") == "data" and "payload" in data:
                            token_transfers = data["payload"]["data"]["Solana"]["TokenTransfers"]
                            
                            for transfer in token_transfers:
                                # Обработка данных о новом токене
                                await process_token_transfer(transfer)
                                
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            # Ждем перед повторным подключением
            await asyncio.sleep(5)

async def process_token_transfer(transfer):
    """Process token transfer data and store in Supabase"""
    try:
        # Извлекаем данные из трансфера
        transaction_hash = transfer["Transaction"]["Hash"]
        block_time = transfer["Block"]["Time"]
        sender = transfer["Transfer"]["Sender"]["Address"]
        receiver = transfer["Transfer"]["Receiver"]["Address"]
        amount = transfer["Transfer"]["Amount"]
        currency = transfer["Transfer"]["Currency"]
        
        # Проверяем, существует ли уже такая транзакция
        result = supabase.table("token_transfers").select("id").eq("transaction_hash", transaction_hash).execute()
        
        if len(result.data) == 0:
            # Сохраняем данные в Supabase
            supabase.table("token_transfers").insert({
                "transaction_hash": transaction_hash,
                "block_time": block_time,
                "sender": sender,
                "receiver": receiver,
                "amount": amount,
                "mint_address": currency["MintAddress"],
                "token_name": currency.get("Name", ""),
                "token_symbol": currency.get("Symbol", ""),
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            logger.info(f"Saved new token transfer: {transaction_hash}")
        else:
            logger.debug(f"Skipped duplicate transaction: {transaction_hash}")
            
    except Exception as e:
        logger.error(f"Error processing token transfer: {str(e)}")

async def main():
    """Main entry point for the worker"""
    try:
        logger.info("Starting Solana token monitor worker...")
        
        # Проверяем подключение к Supabase
        try:
            test_query = supabase.table("token_transfers").select("count", count="exact").limit(1).execute()
            logger.info(f"Connected to Supabase. Current token_transfers count: {test_query.count}")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {str(e)}")
            return
        
        # Запускаем мониторинг токенов
        await monitor_new_tokens()
        
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}")
        
# Запуск мониторинга
if __name__ == "__main__":
    asyncio.run(main())
