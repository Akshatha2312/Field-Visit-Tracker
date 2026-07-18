from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework.generics import ListAPIView, RetrieveAPIView

from .forms import EmployeeProfileForm
from .models import Employee
from .permissions import admin_required, is_admin_user
from .serializers import EmployeeSerializer
from .utils import get_employee_for_user


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
@admin_required
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

    employees = employees.order_by("name")
    paginator = Paginator(employees, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "employee/list.html",
        {
            "employees": page_obj.object_list,
            "page_obj": page_obj,
            "search_query": search_query,
            "role_filter": role_filter,
            "name_filter": name_filter,
        },
    )


@login_required(login_url="login")
@admin_required
def employee_create_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        form_data = request.POST.copy()
        if not username:
            messages.error(request, "Username is required.")
            return render(request, "employee/form.html", {"title": "Add Employee"})

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            messages.error(request, "A user with that username already exists.")
            return render(request, "employee/form.html", {"title": "Add Employee"})

        if not password:
            messages.error(request, "Password is required.")
            return render(request, "employee/form.html", {"title": "Add Employee"})

        user = User.objects.create_user(username=username, password=password)
        employee = Employee.objects.create(
            user=user,
            name=form_data.get("name", "").strip(),
            email=form_data.get("email", "").strip(),
            phone_number=form_data.get("phone_number") or None,
            password=password,
            role=form_data.get("role", Employee.Role.EMPLOYEE),
        )
        messages.success(request, "Employee created successfully.")
        return redirect("employee:list")

    return render(request, "employee/form.html", {"title": "Add Employee"})


@login_required(login_url="login")
@admin_required
def employee_detail_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, "employee/detail.html", {"employee": employee})


@login_required(login_url="login")
@admin_required
def employee_edit_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        new_email = request.POST.get("email", "").strip()
        if employee.user and employee.user.username != username and get_user_model().objects.filter(username=username).exclude(pk=employee.user_id).exists():
            messages.error(request, "A user with that username already exists.")
            return render(request, "employee/form.html", {"title": "Edit Employee", "employee": employee})

        if employee.user is not None:
            if username:
                employee.user.username = username
            if new_email:
                employee.user.email = new_email
            employee.user.save(update_fields=["username", "email"])

        employee.name = request.POST.get("name", "").strip()
        employee.email = new_email
        employee.phone_number = request.POST.get("phone_number") or None
        employee.role = request.POST.get("role", employee.role)
        if password:
            employee.password = password
            if employee.user is not None:
                employee.user.set_password(password)
                employee.user.save(update_fields=["password"])
        employee.save()
        messages.success(request, "Employee updated successfully.")
        return redirect("employee:list")

    return render(request, "employee/form.html", {"title": "Edit Employee", "employee": employee})


@login_required(login_url="login")
@admin_required
def employee_delete_view(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == "POST":
        if employee.user is not None:
            employee.user.delete()
        else:
            employee.delete()
        messages.success(request, "Employee deleted successfully.")
        return redirect("employee:list")

    return render(request, "employee/delete_confirm.html", {"employee": employee})


class EmployeeListView(ListAPIView):
    queryset = Employee.objects.order_by("name")
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        if not is_admin_user(self.request.user):
            raise PermissionDenied
        return super().get_queryset()


class EmployeeDetailView(RetrieveAPIView):
    queryset = Employee.objects.order_by("name")
    serializer_class = EmployeeSerializer

    def get_queryset(self):
        if not is_admin_user(self.request.user):
            raise PermissionDenied
        return super().get_queryset()
