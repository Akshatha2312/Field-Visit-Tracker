from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from rest_framework.generics import ListAPIView, RetrieveAPIView

from .forms import EmployeeProfileForm
from .models import Employee
from .serializers import EmployeeSerializer


def get_employee_for_user(user):
    if hasattr(user, "employee"):
        return user.employee

    # Use single query with Q objects instead of two separate queries
    return Employee.objects.filter(Q(email=user.email) | Q(name=user.username)).first()


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


@login_required(login_url="login")
def employee_list_view(request):
    search_query = request.GET.get("q", "").strip()
    role_filter = request.GET.get("role", "").strip()
    name_filter = request.GET.get("name", "").strip()
    employees = Employee.objects.order_by("name")

    if search_query:
        employees = employees.filter(Q(name__icontains=search_query) | Q(email__icontains=search_query))

    if role_filter:
        employees = employees.filter(role=role_filter)

    if name_filter:
        employees = employees.filter(name__icontains=name_filter)

    return render(
        request,
        "employee/list.html",
        {
            "employees": employees,
            "search_query": search_query,
            "role_filter": role_filter,
            "name_filter": name_filter,
        },
    )


class EmployeeListView(ListAPIView):
    queryset = Employee.objects.order_by("name")
    serializer_class = EmployeeSerializer


class EmployeeDetailView(RetrieveAPIView):
    queryset = Employee.objects.order_by("name")
    serializer_class = EmployeeSerializer
