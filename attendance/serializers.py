from rest_framework import serializers

from .models import Attendance


class AttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "employee", "employee_name", "date", "status", "check_in", "check_out"]
