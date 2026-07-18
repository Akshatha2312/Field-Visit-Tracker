from django import forms
from django.core.validators import RegexValidator

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
            "placeholder": "10-digit number"
        }),
    )

    class Meta:
        model = Employee
        fields = ["name", "email", "phone_number"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "pattern": "[a-zA-Z0-9._%+-]+@gmail\\.com",
                "title": "Please enter a valid Gmail address (example@gmail.com).",
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

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if phone_number:
            try:
                return int(phone_number)
            except ValueError:
                raise forms.ValidationError("Please enter a valid 10-digit mobile number.")
        return None
