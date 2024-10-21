from django.core.management.base import BaseCommand
from support_app.bot import run_bot  # Предполагается, что функция run_bot() определена в bot.py

class Command(BaseCommand):
    help = 'Запуск Telegram-бота'

    def handle(self, *args, **kwargs):
        run_bot()
