from django.contrib import admin

from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "role", "user")
    search_fields = ("name", "email", "user__username")
    list_filter = ("role",)
    ordering = ("name",)
