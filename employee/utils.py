import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Q
from django.template.loader import render_to_string

from .models import Employee

logger = logging.getLogger(__name__)


def get_employee_for_user(user):
    if not user or not getattr(user, "is_authenticated", False):
        return None

    cached_employee = getattr(user, "_cached_employee", None)
    if cached_employee is not None:
        return cached_employee

    if hasattr(user, "employee"):
        employee = user.employee
        setattr(user, "_cached_employee", employee)
        return employee

    employee = Employee.objects.filter(
        Q(email=user.email) | Q(name=user.username)
    ).select_related("user").first()

    if employee is not None:
        setattr(user, "_cached_employee", employee)

    return employee


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
    if not employee or not getattr(employee, "email", None):
        raise ValueError("Employee email is required.")

    context = {
        "employee_name": employee.name,
        "username": employee.user.username if getattr(employee, "user", None) else "",
        "temporary_password": temporary_password,
        "role": employee.role,
        "login_url": login_url,
    }

    html_content = render_to_string(
        "employee/welcome_email.html",
        context,
    )

    text_content = render_to_string(
        "employee/welcome_email.txt",
        context,
    )

    from_email = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER
    
    logger.debug(
        "Preparing to send welcome email to %s from %s using EMAIL_HOST=%s, EMAIL_PORT=%s, EMAIL_USE_TLS=%s",
        employee.email,
        from_email,
        settings.EMAIL_HOST,
        settings.EMAIL_PORT,
        settings.EMAIL_USE_TLS,
    )
    
    message = EmailMultiAlternatives(
        "Welcome to Field Visit Tracker",
        text_content,
        from_email,
        [employee.email],
    )
    message.attach_alternative(html_content, "text/html")

    try:
        result = message.send(fail_silently=False)
        logger.info(
            "Welcome email sent successfully to %s (result=%s)",
            employee.email,
            result,
        )
    except Exception as e:
        logger.exception(
            "Welcome email failed for %s. Error type: %s, Message: %s",
            employee.email,
            type(e).__name__,
            str(e),
        )
        raise