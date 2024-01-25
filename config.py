from dotenv import load_dotenv
import os

load_dotenv()  # Загружаем переменные окружения из файла .env

DATABASE_URL = os.getenv('DATABASE_URL', "sqlite:///./mydatabase.db")
SECRET_KEY = os.getenv('SECRET_KEY', 'defaultsecretkey')
REDIS_URL = 'redis://localhost:6379'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
MODEL_COSTS = {
    "lr_model": 10,
    "gb_model": 20,
}
