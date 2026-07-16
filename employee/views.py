from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import EmployeeProfileForm
from .models import Employee


def get_employee_for_user(user):
    if hasattr(user, "employee"):
        return user.employee

    return Employee.objects.filter(email=user.email).first() or Employee.objects.filter(name=user.username).first()


@login_required(login_url="login")
def profile_view(request):
    employee = get_employee_for_user(request.user)
    if employee is None:
        messages.error(request, "No employee profile is linked to your account.")
        return redirect("dashboard")

    if request.method == "POST":
        form = EmployeeProfileForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile was updated successfully.")
            return redirect("employee:profile")
    else:
        form = EmployeeProfileForm(instance=employee)

    return render(request, "employee/profile.html", {"form": form, "employee": employee})
