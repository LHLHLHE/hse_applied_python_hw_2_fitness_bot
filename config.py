import logging
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
OPEN_WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")
NUTRITIONIX_API_APP_ID = os.getenv("NUTRITIONIX_API_APP_ID")
NUTRITIONIX_API_APP_KEY = os.getenv("NUTRITIONIX_API_APP_KEY")

if not TOKEN:
    raise ValueError("Переменная окружения BOT_TOKEN не установлена!")
if not OPEN_WEATHER_API_KEY:
    raise ValueError(
        "Переменная окружения OPEN_WEATHER_API_KEY не установлена!"
    )
if not NUTRITIONIX_API_APP_ID:
    raise ValueError(
        "Переменная окружения NUTRITIONIX_API_APP_ID не установлена!"
    )
if not NUTRITIONIX_API_APP_KEY:
    raise ValueError(
        "Переменная окружения NUTRITIONIX_API_APP_KEY не установлена!"
    )

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)

logger.addHandler(stream_handler)
