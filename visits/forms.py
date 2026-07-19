import re

from django import forms

from .models import ClientVisit


class ClientVisitForm(forms.ModelForm):
    contact_number = forms.CharField(
        required=True,
        label="Contact Number",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "inputmode": "numeric",
            "pattern": "[0-9]{10}",
            "maxlength": "10",
            "data-validate": "phone",
            "placeholder": "10-digit number",
        }),
    )

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

    def clean_contact_number(self):
        contact_number = (self.cleaned_data.get("contact_number") or "").strip()
        if not re.fullmatch(r"\d{10}", contact_number):
            raise forms.ValidationError("Enter a valid 10-digit mobile number.")
        return contact_number
