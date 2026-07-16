from django.contrib import admin

from .models import ClientVisit


@admin.register(ClientVisit)
class ClientVisitAdmin(admin.ModelAdmin):
    list_display = ("employee", "client_name", "company_name", "visit_date", "status", "created_at")
    search_fields = ("client_name", "company_name", "location", "employee__name")
    list_filter = ("status", "visit_date")
    readonly_fields = ("created_at",)
    ordering = ("-visit_date", "-created_at")
