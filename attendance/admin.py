from django.contrib import admin

from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "status", "check_in", "check_out")
    search_fields = ("employee__name", "employee__email", "status")
    list_filter = ("date", "status")
    ordering = ("-date", "-check_in")
