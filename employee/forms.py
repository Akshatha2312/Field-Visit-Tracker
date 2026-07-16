from django import forms

from .models import Employee


class EmployeeProfileForm(forms.ModelForm):
    username = forms.CharField(required=False, disabled=True, label="Username")
    role = forms.CharField(required=False, disabled=True, label="Role")

    class Meta:
        model = Employee
        fields = ["name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields["username"].initial = self.instance.user.username
            self.fields["role"].initial = self.instance.role
