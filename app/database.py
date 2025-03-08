import os
from supabase import create_client
from dotenv import load_dotenv

# Загрузка переменных из .env файла (для локальной разработки)
load_dotenv()

# Получение переменных окружения
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

# Инициализация клиента Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_connection():
    """Возвращает клиент Supabase"""
    return supabase
