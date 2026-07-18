from django.db.models import Q

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template.loader import render_to_string

from .models import Employee


def get_employee_for_user(user):
    if not user or not getattr(user, "is_authenticated", False):
        return None

    if hasattr(user, "employee"):
        return user.employee

    return Employee.objects.filter(Q(email=user.email) | Q(name=user.username)).first()


def get_user_role(user):
    if not user or not getattr(user, "is_authenticated", False):
        return Employee.Role.EMPLOYEE

    if getattr(user, "is_superuser", False):
        return Employee.Role.ADMIN

    employee = get_employee_for_user(user)
    if employee is not None:
        return employee.role

    return Employee.Role.EMPLOYEE


def send_employee_welcome_email(employee, temporary_password, login_url):
    if not employee or not employee.email:
        raise ValueError("Employee email is required to send a welcome email.")

    context = {
        "employee_name": employee.name,
        "username": employee.user.username if employee.user else "",
        "temporary_password": temporary_password,
        "role": employee.role,
        "login_url": login_url,
    }

    subject = "Welcome to Field Visit Tracker"
    text_body = render_to_string("employee/welcome_email.txt", context)
    html_body = render_to_string("employee/welcome_email.html", context)

    message = EmailMultiAlternatives(
        subject,
        text_body,
        settings.DEFAULT_FROM_EMAIL,
        [employee.email],
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)
