from rest_framework import serializers

from .models import ClientVisit


class ClientVisitSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.name", read_only=True)

    class Meta:
        model = ClientVisit
        fields = [
            "id",
            "employee",
            "employee_name",
            "client_name",
            "company_name",
            "contact_number",
            "location",
            "visit_date",
            "purpose",
            "meeting_notes",
            "status",
            "created_at",
        ]
