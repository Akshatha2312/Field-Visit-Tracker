import calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone
from rest_framework.generics import ListAPIView, RetrieveAPIView

from dashboard.models import ActivityLog
from employee.models import Employee

from .models import Attendance
from .serializers import AttendanceSerializer
from .utils import send_checkin_email, send_checkout_email


def get_employee_for_user(user):
    if hasattr(user, "employee"):
        return user.employee

    # Use single query with Q objects instead of two separate queries
    return Employee.objects.filter(Q(email=user.email) | Q(name=user.username)).first()


def _build_attendance_calendar(employee, year, month):
    if employee is None:
        return []

    first_day = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    # Optimize by only fetching needed fields
    attendance_map = {
        item.date: item
        for item in Attendance.objects.filter(
            employee=employee, date__year=year, date__month=month
        ).only('date', 'status')
    }

    weeks = []
    week = []
    for _ in range(first_day.weekday()):
        week.append(None)

    for day in range(1, last_day + 1):
        current_date = date(year, month, day)
        attendance = attendance_map.get(current_date)
        week.append(
            {
                "date": current_date,
                "status": attendance.status if attendance else "Absent",
                "is_today": current_date == timezone.localdate(),
            }
        )
        if len(week) == 7:
            weeks.append(week)
            week = []

    if week:
        while len(week) < 7:
            week.append(None)
        weeks.append(week)

    return weeks


@login_required(login_url="login")
def attendance_dashboard(request):
    employee = get_employee_for_user(request.user)
    today = timezone.localdate()
    today_attendance = None

    if employee is not None:
        today_attendance = Attendance.objects.filter(employee=employee, date=today).first()

    calendar_weeks = _build_attendance_calendar(employee, today.year, today.month)
    context = {
        "employee": employee,
        "today_attendance": today_attendance,
        "today": today,
        "calendar_weeks": calendar_weeks,
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

        attendance = Attendance.objects.create(
            employee=employee,
            date=today,
            check_in=timezone.now(),
            status=Attendance.Status.CHECKED_IN,
        )
        ActivityLog.objects.create(
            employee=employee,
            activity_type=ActivityLog.ActivityType.CHECK_IN,
            title="Check In",
            description=f"{employee.name} checked in for {today}.",
        )
        send_checkin_email(employee, attendance)
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
        attendance.status = Attendance.Status.CHECKED_OUT
        attendance.save(update_fields=["check_out", "status"])
        ActivityLog.objects.create(
            employee=employee,
            activity_type=ActivityLog.ActivityType.CHECK_OUT,
            title="Check Out",
            description=f"{employee.name} checked out for {today}.",
        )
        send_checkout_email(employee, attendance)
        messages.success(request, "Check-out recorded successfully.")
        return redirect("attendance:history")

    context = {"employee": employee, "attendance": attendance}
    return render(request, "attendance/check_out.html", context)


@login_required(login_url="login")
def attendance_history(request):
    employee = get_employee_for_user(request.user)
    attendances_qs = Attendance.objects.none()

    if employee is not None:
        attendances_qs = Attendance.objects.filter(employee=employee)

    date_filter = request.GET.get("date", "").strip()
    status_filter = request.GET.get("status", "").strip()

    if date_filter:
        attendances_qs = attendances_qs.filter(date=date_filter)

    if status_filter:
        attendances_qs = attendances_qs.filter(status=status_filter)

    attendances = attendances_qs.order_by("-date", "-check_in")
    paginator = Paginator(attendances, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "attendance/history.html",
        {
            "attendances": page_obj.object_list,
            "page_obj": page_obj,
            "date_filter": date_filter,
            "status_filter": status_filter,
        },
    )


class AttendanceListView(ListAPIView):
    queryset = Attendance.objects.select_related("employee").order_by("-date", "-check_in")
    serializer_class = AttendanceSerializer


class AttendanceDetailView(RetrieveAPIView):
    queryset = Attendance.objects.select_related("employee").order_by("-date", "-check_in")
    serializer_class = AttendanceSerializer
