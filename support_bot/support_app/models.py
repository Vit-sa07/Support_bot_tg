from django.db import models
from django.contrib.auth.models import AbstractUser

# Модель клиента
class Client(models.Model):
    telegram_id = models.BigIntegerField(unique=True, verbose_name='ID Telegram')
    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, null=True, blank=True, verbose_name='Фамилия')
    username = models.CharField(max_length=50, null=True, blank=True, verbose_name='Имя пользователя')
    phone_number = models.CharField(max_length=20, null=True, blank=True, verbose_name='Номер телефона')
    role = models.CharField(max_length=20, default='Клиент', verbose_name='Роль')

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return f"{self.first_name} {self.last_name} (@{self.username})"


# Модель специалиста
class Specialist(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='specialist', verbose_name='Клиент')
    role = models.CharField(max_length=30, default='Специалист техподдержки', verbose_name='Роль')

    class Meta:
        verbose_name = 'Специалист'
        verbose_name_plural = 'Специалисты'

    def __str__(self):
        return f"{self.client.first_name} {self.client.last_name} (@{self.client.username})"


# Модель заявки
class Ticket(models.Model):
    STATUS_CHOICES = [
        ('Ожидает', 'Ожидает'),
        ('В работе', 'В работе'),
        ('Выполнено', 'Выполнено'),
        ('Отклонено', 'Отклонено'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='tickets', verbose_name='Клиент')
    specialist = models.ForeignKey(Specialist, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets', verbose_name='Специалист')
    text = models.TextField(verbose_name='Текст заявки')
    anydesk_id = models.CharField(max_length=20, null=True, blank=True, verbose_name='AnyDesk ID')
    file = models.FileField(upload_to='tickets/', null=True, blank=True, verbose_name='Файл')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Ожидает', verbose_name='Статус')

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'

    def __str__(self):
        return f"Заявка {self.id} от {self.client}"


# Модель заявки для АХО
class AHORequest(models.Model):
    STATUS_CHOICES = [
        ('Ожидает', 'Ожидает'),
        ('В работе', 'В работе'),
        ('Сформирован счет', 'Сформирован счет'),
        ('Оплачено', 'Оплачено'),
        ('Выполнено (доставлен)', 'Выполнено (доставлен)'),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='aho_requests', verbose_name='Клиент')
    file = models.FileField(upload_to='aho_requests/', null=True, blank=True, verbose_name='Файл')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Ожидает', verbose_name='Статус')

    class Meta:
        verbose_name = 'Заявка АХО'
        verbose_name_plural = 'Заявки АХО'

    def __str__(self):
        return f"Заявка АХО #{self.id} от {self.client}"


# Модель роли пользователя
class UserRole(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Название роли')

    class Meta:
        verbose_name = 'Роль пользователя'
        verbose_name_plural = 'Роли пользователей'

    def __str__(self):
        return self.name
