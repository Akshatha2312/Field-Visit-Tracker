from django import forms
from django.core.validators import RegexValidator

from .models import Employee


class EmployeeProfileForm(forms.ModelForm):
    username = forms.CharField(required=False, disabled=True, label="Username")
    role = forms.CharField(required=False, disabled=True, label="Role")
    phone_number = forms.IntegerField(
        required=False,
        label="Phone Number",
        min_value=1000000000,
        max_value=999999999999999,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
        error_messages={"invalid": "Enter a valid phone number with 10 to 15 digits."},
    )

    class Meta:
        model = Employee
        fields = ["name", "email", "phone_number"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields["username"].initial = self.instance.user.username
            self.fields["role"].initial = self.instance.role

        for field_name, field in self.fields.items():
            if field_name not in {"username", "role"}:
                field.widget.attrs.setdefault("class", "form-control")
