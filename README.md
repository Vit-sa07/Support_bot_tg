Проект представляет собой многофункционального Telegram-бота для поддержки клиентов, с возможностью создания заявок в отдел ИТ и АХО, отслеживания их статусов, а также взаимодействия со специалистами поддержки. Бот позволяет клиентам отправлять заявки, специалистам управлять их статусами, а администраторам генерировать отчеты по заявкам. Реализована интеграция с базой данных для хранения заявок и пользователей.

#### Основные возможности:
- **Поддержка нескольких отделов**: Клиенты могут выбирать между отделами ИТ и АХО для отправки заявок.
- **Отправка заявок в формате Excel**: Клиенты АХО могут отправлять заявки в виде Excel-файлов.
- **Статусы заявок**: Заявки могут переходить через несколько статусов: "Ожидает", "В работе", "Сформирован счет", "Оплачено", "Выполнено".
- **Уведомления клиентов**: Бот уведомляет клиентов о каждом изменении статуса их заявок.
- **Панель администратора**: Возможность просмотра заявок, фильтрации по статусу и дате, а также генерации отчетов по заявкам в формате Excel.
- **Поддержка Docker**: Возможность развертывания проекта с помощью Docker для удобства управления и масштабируемости.

#### Установка и запуск:
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/your-username/support-requests-bot.git
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Настройте переменные окружения, добавив их в файл `.env`:
   ```
   SUPPORT_CHAT_ID=your_support_chat_id
   SUPPORT_AHO_CHAT_ID=your_aho_support_chat_id
   ```

4. Выполните миграции базы данных:
   ```bash
   python manage.py migrate
   ```

5. Запустите сервер Django:
   ```bash
   python manage.py runserver
   ```

6. Запустите Telegram-бот:
   ```bash
   python manage.py runbot
   ```

7. Для запуска с Docker:
   ```bash
   docker-compose up --build
   ```

---

This project is a multifunctional Telegram bot designed for customer support, enabling the creation of requests for IT and facility management (AHO) departments, tracking request statuses, and interaction with support specialists. The bot allows clients to submit requests, specialists to manage statuses, and administrators to generate reports. The bot integrates with a database to store requests and user information.

#### Key Features:
- **Multi-department support**: Clients can choose between IT and AHO departments to submit requests.
- **Submit requests in Excel format**: AHO department clients can submit requests as Excel files.
- **Request statuses**: Requests go through several statuses: "Pending", "In Progress", "Invoice Created", "Paid", and "Completed".
- **Client notifications**: The bot notifies clients of each status change in their requests.
- **Admin panel**: View, filter requests by status and date, and generate reports in Excel format.
- **Docker support**: The project can be deployed using Docker for ease of management and scalability.

#### Installation and Setup:
1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/support-requests-bot.git
   ```

2. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in the `.env` file:
   ```
   SUPPORT_CHAT_ID=your_support_chat_id
   SUPPORT_AHO_CHAT_ID=your_aho_support_chat_id
   ```

4. Run the database migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the Django server:
   ```bash
   python manage.py runserver
   ```

6. Start the Telegram bot:
   ```bash
   python manage.py runbot
   ```

7. For Docker deployment:
   ```bash
   docker-compose up --build
   ```
