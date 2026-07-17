from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from .models import Employee
from .utils import get_employee_for_user, get_user_role


def is_admin_user(user):
    return get_user_role(user) == Employee.Role.ADMIN


def is_employee_user(user):
    return get_user_role(user) == Employee.Role.EMPLOYEE


def get_scoped_queryset(user, queryset, *, employee_field="employee"):
    if not getattr(user, "is_authenticated", False):
        return queryset.none()

    if is_admin_user(user):
        return queryset

    employee = get_employee_for_user(user)
    if employee is None:
        return queryset.none()

    if employee_field == "employee__user":
        return queryset.filter(employee__user=user)

    return queryset.filter(**{employee_field: employee})


def _user_has_required_role(user, required_role):
    if required_role == Employee.Role.ADMIN:
        return is_admin_user(user)
    return is_employee_user(user) or is_admin_user(user)


def _raise_forbidden_if_not(condition):
    if not condition:
        raise PermissionDenied


def _require_role(required_role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            _raise_forbidden_if_not(_user_has_required_role(request.user, required_role))
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def admin_required(view_func=None):
    if view_func is None:
        return _require_role(Employee.Role.ADMIN)
    return _require_role(Employee.Role.ADMIN)(view_func)


def employee_required(view_func=None):
    if view_func is None:
        return _require_role(Employee.Role.EMPLOYEE)
    return _require_role(Employee.Role.EMPLOYEE)(view_func)


class AdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        _raise_forbidden_if_not(is_admin_user(request.user))
        return super().dispatch(request, *args, **kwargs)


class EmployeeRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        _raise_forbidden_if_not(_user_has_required_role(request.user, Employee.Role.EMPLOYEE))
        return super().dispatch(request, *args, **kwargs)
