from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from employee.models import Employee

from .models import Attendance


def get_employee_for_user(user):
    if hasattr(user, "employee"):
        return user.employee

    return Employee.objects.filter(email=user.email).first() or Employee.objects.filter(name=user.username).first()


@login_required(login_url="login")
def attendance_dashboard(request):
    employee = get_employee_for_user(request.user)
    today = timezone.localdate()
    today_attendance = None

    if employee is not None:
        today_attendance = Attendance.objects.filter(employee=employee, date=today).first()

    context = {
        "employee": employee,
        "today_attendance": today_attendance,
        "today": today,
    }
    return render(request, "attendance/dashboard.html", context)


@login_required(login_url="login")
def check_in(request):
    employee = get_employee_for_user(request.user)
    if employee is None:
        messages.error(request, "No employee profile is linked to your account.")
        return redirect("attendance:dashboard")

    if request.method == "POST":
        today = timezone.localdate()
        if Attendance.objects.filter(employee=employee, date=today).exists():
            messages.warning(request, "You have already checked in today.")
            return redirect("attendance:dashboard")

        Attendance.objects.create(
            employee=employee,
            date=today,
            check_in=timezone.now(),
            status=Attendance.Status.PRESENT,
        )
        messages.success(request, "Check-in recorded successfully.")
        return redirect("attendance:history")

    return render(request, "attendance/check_in.html", {"employee": employee})


@login_required(login_url="login")
def check_out(request):
    employee = get_employee_for_user(request.user)
    if employee is None:
        messages.error(request, "No employee profile is linked to your account.")
        return redirect("attendance:dashboard")

    today = timezone.localdate()
    attendance = Attendance.objects.filter(employee=employee, date=today).first()

    if request.method == "POST":
        if attendance is None:
            messages.warning(request, "You need to check in before checking out.")
            return redirect("attendance:dashboard")
        if attendance.check_out is not None:
            messages.info(request, "You have already checked out today.")
            return redirect("attendance:dashboard")

        attendance.check_out = timezone.now()
        attendance.save(update_fields=["check_out"])
        messages.success(request, "Check-out recorded successfully.")
        return redirect("attendance:history")

    context = {"employee": employee, "attendance": attendance}
    return render(request, "attendance/check_out.html", context)


@login_required(login_url="login")
def attendance_history(request):
    employee = get_employee_for_user(request.user)
    attendances = []

    if employee is not None:
        attendances = Attendance.objects.filter(employee=employee).order_by("-date", "-check_in")

    return render(request, "attendance/history.html", {"attendances": attendances})
