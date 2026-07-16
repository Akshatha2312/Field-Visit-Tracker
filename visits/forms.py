from django import forms

from .models import ClientVisit


class ClientVisitForm(forms.ModelForm):
    class Meta:
        model = ClientVisit
        fields = [
            "client_name",
            "company_name",
            "contact_number",
            "location",
            "visit_date",
            "purpose",
            "meeting_notes",
            "status",
        ]
        widgets = {
            "visit_date": forms.DateInput(attrs={"type": "date"}),
            "purpose": forms.Textarea(attrs={"rows": 3}),
            "meeting_notes": forms.Textarea(attrs={"rows": 3}),
        }
