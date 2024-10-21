import os
import django
import sys
import telebot
from telebot import types
from django.conf import settings
from dotenv import load_dotenv
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'support_bot.settings')
django.setup()

from support_app.models import Client, Ticket, Specialist

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

bot = telebot.TeleBot(TOKEN)

user_state = {}

STATE_WAITING_FOR_NAME = "waiting_for_name"
STATE_WAITING_FOR_PHONE = "waiting_for_phone"

from support_app.handlers import *

MAX_RETRIES = 5

def run_bot():
    retry_count = 0

    while retry_count < MAX_RETRIES:
        try:
            logger.info("Запуск бота...")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            retry_count += 1
            logger.error(f"Ошибка при работе бота: {e}")
            time.sleep(5)
            logger.info(f"Попытка перезапуска ({retry_count}/{MAX_RETRIES})...")

            if retry_count >= MAX_RETRIES:
                logger.critical("Превышено максимальное количество попыток перезапуска. Завершение работы.")
                break

if __name__ == '__main__':
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("Остановка бота.")
