import logging
import re

logger = logging.getLogger(__name__)

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from rest_framework.generics import ListAPIView, RetrieveAPIView

from .forms import EmployeeProfileForm
from .models import Employee
from .permissions import admin_required, is_admin_user
from .serializers import EmployeeSerializer
from .utils import get_employee_for_user, send_employee_welcome_email


def _validate_email_value(email_value):
    email_value = (email_value or "").strip()
    if not email_value:
        return email_value
    try:
        validate_email(email_value)
    except ValidationError as exc:
        raise ValidationError("Please enter a valid email address.") from exc
    return email_value


def _validate_phone_value(phone_value):
    phone_value = (phone_value or "").strip()
    if not phone_value:
        return None
    if not re.fullmatch(r"\d{10}", phone_value):
        raise ValidationError("Enter a valid 10-digit mobile number.")
    return int(phone_value)


def _validate_password_value(password_value):
    password_value = password_value or ""
    if not password_value:
        return password_value
    try:
        validate_password(password_value)
    except ValidationError as exc:
        raise ValidationError("Password must be at least 8 characters and include an uppercase letter, a lowercase letter, a number, and a special character.") from exc
    return password_value


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
    paginator = Paginator(employees, 8)
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

        try:
            email_value = _validate_email_value(form_data.get("email", "").strip())
            phone_value = _validate_phone_value(form_data.get("phone_number", "").strip())
            password_value = _validate_password_value(password)
        except ValidationError as exc:
            messages.error(request, str(exc))
            return render(request, "employee/form.html", {"title": "Add Employee"})

        user = User.objects.create_user(
            username=username,
            password=password,
        )

        employee = Employee.objects.create(
            user=user,
            name=form_data.get("name", "").strip(),
            email=email_value,
            phone_number=phone_value,
            password=password_value,
            role=form_data.get("role", Employee.Role.EMPLOYEE),
        )

        messages.success(request, "Employee created successfully.")

        try:
            send_employee_welcome_email(
                employee,
                password,
                request.build_absolute_uri(reverse("login")),
            )
            logger.info(
                "Welcome email sent successfully for employee: %s (%s)",
                employee.name,
                employee.email,
            )
        except Exception as e:
            logger.exception(
                "Failed to send welcome email for employee %s (%s). Exception: %s",
                employee.name,
                employee.email,
                str(e),
            )

            messages.warning(
                request,
                "Employee was created successfully, but the welcome email could not be sent.",
            )

        return redirect("employee:list")

    return render(
        request,
        "employee/form.html",
        {
            "title": "Add Employee",
        },
    )


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

        try:
            email_value = _validate_email_value(new_email)
            phone_value = _validate_phone_value(request.POST.get("phone_number", "").strip())
            password_value = _validate_password_value(password) if password else password
        except ValidationError as exc:
            messages.error(request, str(exc))
            return render(request, "employee/form.html", {"title": "Edit Employee", "employee": employee})

        if employee.user is not None:
            if username:
                employee.user.username = username
            if new_email:
                employee.user.email = email_value
            employee.user.save(update_fields=["username", "email"])

        employee.name = request.POST.get("name", "").strip()
        employee.email = email_value
        employee.phone_number = phone_value
        employee.role = request.POST.get("role", employee.role)
        if password:
            employee.password = password_value
            if employee.user is not None:
                employee.user.set_password(password_value)
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
