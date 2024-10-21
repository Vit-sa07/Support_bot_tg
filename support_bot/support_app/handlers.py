from telebot import types
from support_app.models import Client, Ticket, Specialist
from .bot import bot, user_state, STATE_WAITING_FOR_NAME, STATE_WAITING_FOR_PHONE
from dotenv import load_dotenv
import os
import logging
import pandas as pd
from io import BytesIO
from .models import AHORequest

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
load_dotenv()

# Состояния для подачи заявки
STATE_CREATING_TICKET = "creating_ticket"
STATE_WAITING_FOR_ANYDESK = "waiting_for_anydesk"
SUPPORT_CHAT_ID = os.getenv('SUPPORT_CHAT_ID')
SUPPORT_AHO_CHAT_ID = os.getenv('SUPPORT_AHO_CHAT_ID')

# Функция для создания клавиатуры после регистрации
def get_department_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    it_button = types.KeyboardButton("ИТ")
    aho_button = types.KeyboardButton("АХО")
    markup.add(it_button, aho_button)
    return markup

# Функция для создания клавиатуры для специалиста
def get_specialist_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    waiting_tickets_button = types.KeyboardButton("📂 Заявки в ожидании")
    in_progress_tickets_button = types.KeyboardButton("🔧 Заявки в работе")
    user_list_button = types.KeyboardButton("👥 Список пользователей")
    report_button = types.KeyboardButton("📊 Отчет за месяц")
    markup.add(waiting_tickets_button, in_progress_tickets_button)
    markup.add(user_list_button, report_button)
    return markup


# Функция для создания меню ИТ с кнопкой "Назад"
def get_it_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    ticket_button = types.KeyboardButton("📝 Подать заявку")
    status_button = types.KeyboardButton("📊 Статус заявки")
    my_tickets_button = types.KeyboardButton("📂 Мои заявки")
    contacts_button = types.KeyboardButton("📞 Контакты")
    back_button = types.KeyboardButton("🔙 Назад")
    markup.add(ticket_button, status_button)
    markup.add(my_tickets_button, contacts_button)
    markup.add(back_button)
    return markup

# Обработчик для кнопки "🔙 Назад"
@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def go_back_to_main_menu(message):
    user_id = message.chat.id

    if user_id in ticket_info:
        del ticket_info[user_id]

    bot.send_message(user_id, "Вы вернулись в главное меню. Выберите интересующий отдел:", reply_markup=get_department_keyboard())
    logger.info(f"Пользователь {user_id} вернулся в главное меню.")





@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user = Client.objects.filter(telegram_id=user_id).first()

    if user:
        specialist = Specialist.objects.filter(client=user).first()

        if specialist:
            bot.send_message(user_id, "Добро пожаловать в админ-меню специалиста! Выберите действие:",
                             reply_markup=get_specialist_keyboard())
        else:
            bot.send_message(user_id, f"Выберите интересующий отдел:",
                             reply_markup=get_department_keyboard())
    else:
        user_state[user_id] = STATE_WAITING_FOR_NAME
        bot.send_message(user_id, "Добро пожаловать! Пожалуйста, введите ваше полное имя (ФИО).")


# Обработчик получения ФИО
@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == STATE_WAITING_FOR_NAME)
def get_name(message):
    user_id = message.chat.id
    full_name = message.text
    user_state[user_id] = {'full_name': full_name, 'state': STATE_WAITING_FOR_PHONE}
    bot.send_message(user_id, "Отлично! Теперь отправьте ваш номер телефона или нажмите кнопку ниже для его отправки.",
                     reply_markup=request_phone_keyboard())

# Функция создания клавиатуры для отправки номера телефона
def request_phone_keyboard():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button_phone = types.KeyboardButton(text="Отправить номер телефона", request_contact=True)
    markup.add(button_phone)
    return markup

# Обработчик получения номера телефона
@bot.message_handler(content_types=['contact'])
def contact(message):
    user_id = message.chat.id
    user_info = user_state.get(user_id, None)
    if user_info and user_info.get('state') == STATE_WAITING_FOR_PHONE:
        full_name = user_info.get('full_name')
        telegram_id = message.contact.user_id
        phone_number = message.contact.phone_number
        name_parts = full_name.split()
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        user, created = Client.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={'first_name': first_name, 'last_name': last_name, 'username': message.from_user.username, 'phone_number': phone_number}
        )
        user.phone_number = phone_number
        user.save()
        del user_state[user_id]
        bot.send_message(user_id, f"Спасибо, {full_name}, ваш номер сохранен!\nВыберите интересующий отдел:",
                         reply_markup=get_department_keyboard())
    else:
        bot.send_message(user_id, "Для регистрации используйте команду /start и следуйте инструкциям.")

# Обработчик кнопки "ИТ"
@bot.message_handler(func=lambda message: message.text == "ИТ")
def it_menu(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Вы выбрали отдел ИТ. Выберите одно из действий ниже:", reply_markup=get_it_menu_keyboard())

# Функция для создания меню АХО с кнопкой "Назад"
def get_aho_menu_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    submit_request_button = types.KeyboardButton("📄 Отправить заявку (Excel)")
    back_button = types.KeyboardButton("🔙 Назад")
    markup.add(submit_request_button)
    markup.add(back_button)
    return markup

# Обработчик для кнопки "АХО"
@bot.message_handler(func=lambda message: message.text == "АХО")
def show_aho_menu(message):
    bot.send_message(message.chat.id, "Вы вошли в меню АХО. Пожалуйста, отправьте вашу заявку в виде Excel файла.", reply_markup=get_aho_menu_keyboard())
    logger.info(f"Пользователь {message.chat.id} открыл меню АХО.")


# ============================================== ЛОГИКА ЗАЯВКИ ==============================================
ticket_info = {}

STATE_DESCRIPTION = "description"
STATE_ANYDESK = "anydesk"


# Обработчик нажатия кнопки "📝 Подать заявку"
@bot.message_handler(func=lambda message: message.text == "📝 Подать заявку")
def create_ticket_request(message):
    user_id = message.chat.id
    user = Client.objects.filter(telegram_id=user_id).first()

    if user:
        ticket_info[user_id] = {'description': None, 'photo': None, 'anydesk_id': None}
        bot.send_message(user_id, "Пожалуйста, опишите вашу проблему. Отправьте текстовое описание или фото с текстом.",
                         reply_markup=get_back_button())
        bot.register_next_step_handler(message, handle_ticket_description)
        logger.info(f"Пользователь {user_id} начал создание заявки.")
    else:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /start.")
        logger.warning(f"Пользователь {user_id} попытался создать заявку без регистрации.")

# Обработчик для получения описания заявки (текста или фото)
def handle_ticket_description(message):
    user_id = message.chat.id
    if user_id not in ticket_info or message.text == "🔙 Назад":
        go_back_to_department_menu(message)
        return

    if message.content_type == 'text':
        ticket_info[user_id]['description'] = message.text
    elif message.content_type == 'photo':
        ticket_text = message.caption if message.caption else "Фото заявки без текста"
        photo_id = message.photo[-1].file_id
        ticket_info[user_id]['description'] = ticket_text
        ticket_info[user_id]['photo'] = photo_id

    bot.send_message(user_id, "Введите ваш ID AnyDesk для удаленного решения проблемы (только цифры).",
                     reply_markup=get_back_button())
    bot.register_next_step_handler(message, handle_anydesk_id)
    logger.info(f"Пользователь {user_id} отправил описание заявки. Переход к вводу ID AnyDesk.")

# Обработчик для получения ID AnyDesk
def handle_anydesk_id(message):
    user_id = message.chat.id
    if message.text == "🔙 Назад":
        go_back_to_department_menu(message)
        return

    if not message.text.isdigit():
        bot.send_message(user_id, "Пожалуйста, введите ваш ID AnyDesk, используя только цифры.",
                         reply_markup=get_back_button())
        bot.register_next_step_handler(message, handle_anydesk_id)
        return

    anydesk_id = message.text
    ticket_info[user_id]['anydesk_id'] = anydesk_id
    user = Client.objects.filter(telegram_id=user_id).first()

    ticket = Ticket.objects.create(client=user, text=ticket_info[user_id]['description'], anydesk_id=anydesk_id)

    if ticket_info[user_id]['photo']:
        file_info = bot.get_file(ticket_info[user_id]['photo'])
        downloaded_file = bot.download_file(file_info.file_path)

        directory = 'tickets'
        if not os.path.exists(directory):
            os.makedirs(directory)

        file_path = f'{directory}/ticket_{ticket.id}.jpg'
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        ticket.file = file_path
        ticket.save()
        logger.info(f"Пользователь {user_id} прикрепил фото к заявке #{ticket.id}.")

    del ticket_info[user_id]

    bot.send_message(user_id, f"Заявка #{ticket.id} успешно создана и отправлена в техподдержку.",
                     reply_markup=get_it_menu_keyboard())
    logger.info(f"Пользователь {user_id} создал заявку #{ticket.id}. Отправляем в чат администраторов.")

    send_ticket_to_support_chat(ticket)

# Обработчик для кнопки "🔙 Назад"
@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def go_back_to_department_menu(message):
    user_id = message.chat.id

    if user_id in ticket_info:
        del ticket_info[user_id]

    bot.send_message(user_id, "Вы вернулись в главное меню. Выберите интересующий отдел:",
                     reply_markup=get_department_keyboard())
    logger.info(f"Пользователь {user_id} вернулся в главное меню.")

# Функция для создания кнопки "🔙 Назад"
def get_back_button():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    back_button = types.KeyboardButton("🔙 Назад")
    markup.add(back_button)
    return markup


# Функция отправки заявки в чат администраторов с кнопками
def send_ticket_to_support_chat(ticket):
    support_chat_id = SUPPORT_CHAT_ID

    markup = types.InlineKeyboardMarkup()
    accept_button = types.InlineKeyboardButton("✅ Принять заявку", callback_data=f'accept_{ticket.id}')
    reject_button = types.InlineKeyboardButton("❌ Отклонить заявку", callback_data=f'reject_{ticket.id}')
    markup.add(accept_button, reject_button)

    message_text = (
        f"Новая заявка #{ticket.id}\n"
        f"Клиент: {ticket.client.first_name} {ticket.client.last_name}\n"
        f"Проблема: {ticket.text}\n"
        f"AnyDesk ID: {ticket.anydesk_id}\n"
        f"Статус: {ticket.status}"
    )

    if ticket.file:
        file_path = ticket.file.path
        with open(file_path, 'rb') as file:
            bot.send_photo(support_chat_id, photo=file, caption=message_text, reply_markup=markup)
        logger.info(f"Заявка #{ticket.id} с фото отправлена в чат администраторов.")
    else:
        bot.send_message(support_chat_id, message_text, reply_markup=markup)
        logger.info(f"Заявка #{ticket.id} без фото отправлена в чат администраторов.")



# Обработчик для обработки нажатия на inline-кнопки принятия и отклонения заявки
@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_") or call.data.startswith("reject_"))
def handle_ticket_action(call):
    ticket_id = int(call.data.split('_')[1])
    user_id = call.from_user.id
    ticket = Ticket.objects.filter(id=ticket_id).first()
    specialist = Specialist.objects.filter(client__telegram_id=user_id).first()

    if not ticket:
        bot.answer_callback_query(call.id, "Заявка не найдена.")
        return

    if not specialist:
        bot.answer_callback_query(call.id, "Вы не зарегистрированы как специалист.")
        return

    if call.data.startswith("accept_"):
        ticket.status = "В работе"
        ticket.specialist = specialist
        ticket.save()

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f"Заявка #{ticket.id} принята специалистом: {specialist.client.first_name}. Статус: В работе.", reply_markup=None)

        bot.send_message(ticket.client.telegram_id, f"Ваша заявка #{ticket.id} принята специалистом {specialist.client.first_name}. Специалист скоро свяжется с вами.")

        markup = types.InlineKeyboardMarkup()
        chat_button = types.InlineKeyboardButton("💬 Перейти в чат", url=f"tg://user?id={ticket.client.telegram_id}")
        complete_button = types.InlineKeyboardButton("✅ Завершить заявку", callback_data=f'complete_{ticket.id}')
        markup.add(chat_button, complete_button)

        bot.send_message(call.message.chat.id, f"Свяжитесь с клиентом {ticket.client.first_name} {ticket.client.last_name} по заявке #{ticket.id}.",
                         reply_markup=markup)
        logger.info(f"Заявка #{ticket.id} принята специалистом {specialist.client.first_name}. Создан переход в чат с клиентом.")

    elif call.data.startswith("reject_"):
        ticket.status = "Отклонено"
        ticket.save()

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f"Заявка #{ticket.id} отклонена специалистом: {specialist.client.first_name}.", reply_markup=None)

        bot.send_message(ticket.client.telegram_id, f"Ваша заявка #{ticket.id} отклонена специалистом. Пожалуйста, свяжитесь с техподдержкой для получения дополнительной информации.")
        logger.info(f"Заявка #{ticket.id} отклонена специалистом {specialist.client.first_name}.")

# Обработчик для завершения заявки
@bot.callback_query_handler(func=lambda call: call.data.startswith("complete_"))
def complete_ticket(call):
    ticket_id = int(call.data.split('_')[1])
    user_id = call.from_user.id
    ticket = Ticket.objects.filter(id=ticket_id).first()

    if not ticket:
        bot.answer_callback_query(call.id, "Заявка не найдена.")
        return

    if ticket.specialist and ticket.specialist.client.telegram_id == user_id:
        ticket.status = "Выполнено"
        ticket.save()

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text=f"Заявка #{ticket.id} завершена специалистом {ticket.specialist.client.first_name}.", reply_markup=None)
        bot.send_message(ticket.client.telegram_id, f"Ваша заявка #{ticket.id} выполнена. Спасибо, что воспользовались нашей техподдержкой.")
        logger.info(f"Заявка #{ticket.id} успешно завершена специалистом {ticket.specialist.client.first_name}.")
    else:
        bot.answer_callback_query(call.id, "Только назначенный специалист может завершить эту заявку.")

# ============================================== ЛОГИКА КНОПОК ==============================================

# Обработчик для кнопки "📊 Статус заявки"
@bot.message_handler(func=lambda message: message.text == "📊 Статус заявки")
def check_ticket_status(message):
    user_id = message.chat.id
    user = Client.objects.filter(telegram_id=user_id).first()
    if not user:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /start.")
        return

    # Получаем последнюю заявку пользователя
    last_ticket = Ticket.objects.filter(client=user).order_by('-created_at').first()
    if not last_ticket:
        bot.send_message(user_id, "😔 У вас нет активных заявок. Нажмите '📝 Подать заявку', чтобы создать новую.")
    else:
        status_emoji = {
            'Ожидает': '🕓',
            'В работе': '🔧',
            'Выполнено': '✅',
            'Отклонено': '❌'
        }
        status_message = (
            f"📊 **Статус вашей последней заявки #{last_ticket.id}**\n\n"
            f"📝 **Описание:** {last_ticket.text}\n"
            f"💼 **Статус:** {status_emoji.get(last_ticket.status, '')} {last_ticket.status}\n"
            f"📅 **Дата создания:** {last_ticket.created_at.strftime('%d-%m-%Y %H:%M')}"
        )
        bot.send_message(user_id, status_message, parse_mode='Markdown')
        logger.info(f"Пользователь {user_id} запросил статус последней заявки.")


# Обработчик для кнопки "📂 Мои заявки"
@bot.message_handler(func=lambda message: message.text == "📂 Мои заявки")
def show_my_tickets(message):
    user_id = message.chat.id
    user = Client.objects.filter(telegram_id=user_id).first()
    if not user:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /start.")
        return

    tickets = Ticket.objects.filter(client=user).order_by('-created_at')
    if not tickets:
        bot.send_message(user_id, "😔 У вас нет активных заявок. Нажмите '📝 Подать заявку', чтобы создать новую.")
    else:
        ticket_list = ""
        status_emoji = {
            'Ожидает': '🕓',
            'В работе': '🔧',
            'Выполнено': '✅',
            'Отклонено': '❌'
        }
        for ticket in tickets:
            ticket_list += (
                f"🔹 **Заявка #{ticket.id}**\n"
                f"📝 **Описание:** {ticket.text[:30]}...\n"
                f"💼 **Статус:** {status_emoji.get(ticket.status, '')} {ticket.status}\n"
                f"📅 **Дата создания:** {ticket.created_at.strftime('%d-%m-%Y %H:%M')}\n\n"
            )

        bot.send_message(user_id, f"📂 **Ваши заявки:**\n\n{ticket_list}", parse_mode='Markdown')
        logger.info(f"Пользователь {user_id} запросил список своих заявок.")


# Обработчик для кнопки "📞 Контакты"
@bot.message_handler(func=lambda message: message.text == "📞 Контакты")
def show_contacts(message):
    user_id = message.chat.id
    user = Client.objects.filter(telegram_id=user_id).first()
    if not user:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /start.")
        return
    specialists = Specialist.objects.all()
    if not specialists:
        bot.send_message(user_id, "😔 В данный момент нет доступных специалистов.")
    else:
        markup = types.InlineKeyboardMarkup()
        for specialist in specialists:
            button = types.InlineKeyboardButton(
                text=f"{specialist.client.last_name} {specialist.client.first_name}",
                url=f"tg://user?id={specialist.client.telegram_id}")
            markup.add(button)
        bot.send_message(user_id, "👨‍💻 **Выберите специалиста для связи:**", reply_markup=markup, parse_mode='Markdown')
        logger.info(f"Пользователь {user_id} запросил список специалистов.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("contact_specialist_"))
def contact_specialist(call):
    specialist_id = int(call.data.split('_')[2])
    user_id = call.from_user.id

    specialist = Client.objects.filter(telegram_id=specialist_id).first()
    if not specialist:
        bot.answer_callback_query(call.id, "Специалист не найден.")
        return

    chat_url = f"tg://user?id={specialist.telegram_id}"
    bot.answer_callback_query(call.id)
    bot.send_message(user_id, f"Переходим в чат с {specialist.last_name} {specialist.first_name}.", reply_markup=None)
    bot.send_message(user_id, chat_url, disable_web_page_preview=True)
    logger.info(f"Пользователь {user_id} выбрал связь со специалистом {specialist.first_name} {specialist.last_name}.")


# ============================================== ЛОГИКА АХО ==============================================

@bot.message_handler(func=lambda message: message.text == "📄 Отправить заявку (Excel)")
def request_excel_file(message):
    user_id = message.chat.id
    user = Client.objects.filter(telegram_id=user_id).first()

    if user:
        bot.send_message(user_id, "Пожалуйста, отправьте вашу заявку в формате Excel (.xlsx).")
        logger.info(f"Пользователь {user_id} нажал кнопку '📄 Отправить заявку (Excel)'. Ожидание загрузки файла.")
    else:
        bot.send_message(user_id, "Сначала зарегистрируйтесь с помощью команды /start.")
        logger.warning(f"Пользователь {user_id} попытался отправить заявку без регистрации.")



# Обработчик для получения Excel файла
@bot.message_handler(content_types=['document'])
def handle_excel_file(message):
    user_id = message.chat.id
    user = Client.objects.filter(telegram_id=user_id).first()

    if message.document.mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        folder_name = 'aho_requests'
        file_name = os.path.join(folder_name, message.document.file_name)

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            logger.info(f"Создана директория: {folder_name}")

        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        request = AHORequest.objects.create(client=user, file=file_name)

        send_aho_request_to_support_chat(request)

        bot.send_message(user_id, f"Ваша заявка #{request.id} успешно отправлена в АХО. Ожидайте ответа.", reply_markup=get_department_keyboard())
        logger.info(f"Пользователь {user_id} отправил заявку в АХО. Файл: {file_name}.")
    else:
        bot.send_message(user_id, "Пожалуйста, отправьте файл в формате Excel (.xlsx).")
        logger.warning(f"Пользователь {user_id} попытался отправить неподдерживаемый файл.")


# Функция отправки заявки АХО в чат администраторов с кнопками
def send_aho_request_to_support_chat(request):
    support_chat_id = SUPPORT_AHO_CHAT_ID

    message_text = (
        f"Новая заявка АХО #{request.id}\n"
        f"Клиент: {request.client.first_name} {request.client.last_name} (@{request.client.username})\n"
        f"Статус: {request.status}\n"
        f"Дата создания: {request.created_at.strftime('%Y-%m-%d %H:%M')}"
    )

    markup = types.InlineKeyboardMarkup()
    if request.status == 'Ожидает':
        markup.add(types.InlineKeyboardButton("✅ Взять в работу", callback_data=f'aho_accept_{request.id}'))
    elif request.status == 'В работе':
        markup.add(types.InlineKeyboardButton("💵 Сформировать счет", callback_data=f'aho_invoice_{request.id}'))
    elif request.status == 'Сформирован счет':
        markup.add(types.InlineKeyboardButton("💳 Оплачено", callback_data=f'aho_paid_{request.id}'))
    elif request.status == 'Оплачено':
        markup.add(types.InlineKeyboardButton("📦 Выполнено (доставлен)", callback_data=f'aho_completed_{request.id}'))

    if request.file:
        bot.send_document(support_chat_id, document=open(request.file.path, 'rb'), caption=message_text, reply_markup=markup)
        logger.info(f"Заявка АХО #{request.id} с файлом отправлена в чат администраторов АХО.")
    else:
        bot.send_message(support_chat_id, message_text, reply_markup=markup)
        logger.info(f"Заявка АХО #{request.id} без файла отправлена в чат администраторов АХО.")


# Обработчик для обработки нажатия на inline-кнопки изменения статуса заявки АХО
@bot.callback_query_handler(func=lambda call: call.data.startswith("aho_"))
def handle_aho_status_change(call):
    request_id = int(call.data.split('_')[2])
    request = AHORequest.objects.filter(id=request_id).first()

    if not request:
        bot.answer_callback_query(call.id, "Заявка не найдена.")
        return

    if call.data.startswith("aho_accept_"):
        request.status = 'В работе'
        notification = f"Ваша заявка #{request.id} была принята в работу."
    elif call.data.startswith("aho_invoice_"):
        request.status = 'Сформирован счет'
        notification = f"По вашей заявке #{request.id} был сформирован счет."
    elif call.data.startswith("aho_paid_"):
        request.status = 'Оплачено'
        notification = f"Счет по вашей заявке #{request.id} был оплачен."
    elif call.data.startswith("aho_completed_"):
        request.status = 'Выполнено (доставлен)'
        notification = f"Ваша заявка #{request.id} выполнена и товар доставлен."

    request.save()

    bot.send_message(request.client.telegram_id, notification)

    bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id,
                             caption=(
                                 f"Заявка АХО #{request.id}\n"
                                 f"Клиент: {request.client.first_name} {request.client.last_name} (@{request.client.username})\n"
                                 f"Статус: {request.status}\n"
                                 f"Дата создания: {request.created_at.strftime('%Y-%m-%d %H:%M')}"
                             ),
                             reply_markup=create_aho_buttons(request))
    logger.info(f"Статус заявки АХО #{request.id} изменен на '{request.status}'.")
    bot.answer_callback_query(call.id, f"Статус изменен на '{request.status}'.")


# Функция для создания кнопок изменения статусов заявки АХО
def create_aho_buttons(request):
    markup = types.InlineKeyboardMarkup()
    if request.status == 'Ожидает':
        markup.add(types.InlineKeyboardButton("✅ Взять в работу", callback_data=f'aho_accept_{request.id}'))
    elif request.status == 'В работе':
        markup.add(types.InlineKeyboardButton("💵 Сформировать счет", callback_data=f'aho_invoice_{request.id}'))
    elif request.status == 'Сформирован счет':
        markup.add(types.InlineKeyboardButton("💳 Оплачено", callback_data=f'aho_paid_{request.id}'))
    elif request.status == 'Оплачено':
        markup.add(types.InlineKeyboardButton("📦 Выполнено (доставлен)", callback_data=f'aho_completed_{request.id}'))
    return markup



# ============================================== ЛОГИКА АДМИНА ==============================================

# Обработчик для просмотра заявок в ожидании
@bot.message_handler(func=lambda message: message.text == "📂 Заявки в ожидании")
def show_waiting_tickets(message):
    user_id = message.chat.id
    specialist = Specialist.objects.filter(client__telegram_id=user_id).first()

    if specialist:
        tickets = Ticket.objects.filter(status="Ожидает").all()
        if tickets:
            response = "Заявки в ожидании:\n\n"
            for ticket in tickets:
                response += f"Заявка #{ticket.id}: {ticket.client.first_name} {ticket.client.last_name}\nПроблема: {ticket.text}\n\n"
            bot.send_message(user_id, response)
        else:
            bot.send_message(user_id, "Нет заявок в ожидании.")
    else:
        bot.send_message(user_id, "Вы не зарегистрированы как специалист.")


# Обработчик для просмотра заявок в работе
@bot.message_handler(func=lambda message: message.text == "🔧 Заявки в работе")
def show_in_progress_tickets(message):
    user_id = message.chat.id
    specialist = Specialist.objects.filter(client__telegram_id=user_id).first()

    if specialist:
        tickets = Ticket.objects.filter(status="В работе", specialist=specialist).all()
        if tickets:
            response = "Заявки в работе:\n\n"
            for ticket in tickets:
                response += f"Заявка #{ticket.id}: {ticket.client.first_name} {ticket.client.last_name}\nПроблема: {ticket.text}\n\n"
            bot.send_message(user_id, response)
        else:
            bot.send_message(user_id, "У вас нет заявок в работе.")
    else:
        bot.send_message(user_id, "Вы не зарегистрированы как специалист.")

# Обработчик для просмотра списка пользователей
@bot.message_handler(func=lambda message: message.text == "👥 Список пользователей")
def show_user_list(message):
    user_id = message.chat.id
    specialist = Specialist.objects.filter(client__telegram_id=user_id).first()

    if specialist:
        users = Client.objects.all()
        response = "Список пользователей:\n\n"
        for user in users:
            response += f"Имя: {user.first_name} {user.last_name} (@{user.username})\nТелеграм ID: {user.telegram_id}\n\n"
        bot.send_message(user_id, response)
    else:
        bot.send_message(user_id, "Вы не зарегистрированы как специалист.")

# Обработчик для создания отчета за месяц
@bot.message_handler(func=lambda message: message.text == "📊 Отчет за месяц")
def request_report_month(message):
    user_id = message.chat.id
    specialist = Specialist.objects.filter(client__telegram_id=user_id).first()

    if specialist:
        bot.send_message(user_id, "Введите месяц и год для отчета в формате MM-YYYY (например, 09-2024).")
        bot.register_next_step_handler(message, generate_monthly_report)
    else:
        bot.send_message(user_id, "Вы не зарегистрированы как специалист.")


# Генерация отчета в формате Excel
def generate_monthly_report(message):
    user_id = message.chat.id
    date_input = message.text

    try:
        month, year = map(int, date_input.split('-'))
        start_date = pd.Timestamp(year=year, month=month, day=1)
        end_date = pd.Timestamp(year=year, month=month, day=1) + pd.DateOffset(months=1) - pd.DateOffset(days=1)

        tickets = Ticket.objects.filter(created_at__range=[start_date, end_date])

        if tickets:
            data = []
            for ticket in tickets:
                data.append({
                    'ID заявки': ticket.id,
                    'Клиент': f"{ticket.client.first_name} {ticket.client.last_name}",
                    'Проблема': ticket.text,
                    'Статус': ticket.status,
                    'Дата создания': ticket.created_at.strftime('%Y-%m-%d %H:%M')
                })

            df = pd.DataFrame(data)

            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Отчет')

            excel_buffer.seek(0)
            excel_buffer.name = f"Отчет_{date_input}.xlsx"

            bot.send_document(user_id, document=excel_buffer, caption=f"Отчет за {date_input}")
            logger.info(f"Отчет за {date_input} отправлен специалисту.")
        else:
            bot.send_message(user_id, f"За {date_input} нет заявок.")
    except ValueError:
        bot.send_message(user_id, "Неправильный формат даты. Введите дату в формате MM-YYYY.")
