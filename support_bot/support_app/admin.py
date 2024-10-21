from django.contrib import admin
from .models import Client, Specialist, Ticket, UserRole, AHORequest
import pandas as pd
from django.http import HttpResponse
from django.urls import path
from datetime import datetime

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'username', 'telegram_id', 'phone_number', 'role')
    search_fields = ('first_name', 'last_name', 'username', 'telegram_id')
    list_filter = ('role',)


@admin.register(Specialist)
class SpecialistAdmin(admin.ModelAdmin):
    list_display = ('client', 'role')
    search_fields = ('client__first_name', 'client__last_name', 'client__username')
    list_filter = ('role',)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'specialist', 'status', 'created_at')
    search_fields = ('client__first_name', 'client__last_name', 'client__username', 'anydesk_id', 'text')
    list_filter = ('status', 'created_at')
    readonly_fields = ['created_at']  # Исправлено


@admin.register(AHORequest)
class AHORequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'status', 'created_at')
    search_fields = ('client__first_name', 'client__last_name', 'client__username')
    list_filter = ('status', 'created_at')
    readonly_fields = ['created_at']  # Исправлено
    change_list_template = "admin/report_download.html"  # Шаблон для отчета

    def changelist_view(self, request, extra_context=None):
        current_year = datetime.now().year
        extra_context = extra_context or {}
        extra_context['current_year'] = current_year  # Передаем текущий год в шаблон
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('download-report/', self.admin_site.admin_view(self.download_report),
                 name="support_app_ahorequest_download-report"),
        ]
        return custom_urls + urls

    def download_report(self, request):
        # Получаем месяц и год из GET параметров
        month = request.GET.get('month')
        year = request.GET.get('year')

        if not month or not year:
            self.message_user(request, "Пожалуйста, укажите месяц и год.")
            return HttpResponse(status=400)

        # Формируем дату начала и конца выбранного месяца
        start_date = datetime(year=int(year), month=int(month), day=1)
        end_date = pd.Timestamp(year=int(year), month=int(month), day=1) + pd.DateOffset(months=1) - pd.DateOffset(
            days=1)

        # Извлекаем заявки АХО за выбранный период
        requests = AHORequest.objects.filter(created_at__range=[start_date, end_date])

        if not requests.exists():
            self.message_user(request, "За данный период нет заявок.")
            return HttpResponse(status=400)

        # Генерируем Excel файл с заявками
        df = pd.DataFrame(
            list(requests.values('id', 'client__first_name', 'client__last_name', 'file', 'status', 'created_at')))

        # Удаляем временную зону из поля 'created_at'
        df['created_at'] = df['created_at'].apply(lambda x: x.replace(tzinfo=None))

        df.columns = ['ID Заявки', 'Имя клиента', 'Фамилия клиента', 'Файл', 'Статус', 'Дата создания']

        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = f'attachment; filename="aho_report_{month}_{year}.xlsx"'

        # Записываем данные в Excel
        with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Отчет', index=False)

        return response


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
