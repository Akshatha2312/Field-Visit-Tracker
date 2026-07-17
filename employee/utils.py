from django.db.models import Q

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
