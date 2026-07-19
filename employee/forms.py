import re

from django import forms
from django.core.validators import validate_email

from .models import Employee


class EmployeeProfileForm(forms.ModelForm):
    username = forms.CharField(required=False, disabled=True, label="Username")
    role = forms.CharField(required=False, disabled=True, label="Role")
    phone_number = forms.CharField(
        required=False,
        label="Phone Number",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "inputmode": "numeric",
            "pattern": "[0-9]{10}",
            "minlength": "10",
            "maxlength": "10",
            "title": "Please enter a valid 10-digit mobile number.",
            "placeholder": "10-digit number",
            "data-validate": "phone",
        }),
    )

    class Meta:
        model = Employee
        fields = ["name", "email", "phone_number"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "pattern": "^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$",
                "title": "Please enter a valid email address.",
                "data-validate": "email",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields["username"].initial = self.instance.user.username
            self.fields["role"].initial = self.instance.role

        for field_name, field in self.fields.items():
            if field_name not in {"username", "role"}:
                field.widget.attrs.setdefault("class", "form-control")

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            return email
        try:
            validate_email(email)
        except forms.ValidationError:
            raise forms.ValidationError("Please enter a valid email address.")
        return email

    def clean_phone_number(self):
        phone_number = (self.cleaned_data.get("phone_number") or "").strip()
        if not phone_number:
            return None
        if not re.fullmatch(r"\d{10}", phone_number):
            raise forms.ValidationError("Enter a valid 10-digit mobile number.")
        return int(phone_number)
