from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from attendance.models import Attendance
from dashboard.models import ActivityLog
from employee.models import Employee
from visits.models import ClientVisit

from .csv_utils import build_csv_response
from .excel_utils import build_excel_response
from .pdf_utils import build_pdf_response


def _get_report_context(request):
    employees = Employee.objects.order_by('name').only('id', 'name')

    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    employee_id = request.GET.get('employee', '').strip()
    visit_status = request.GET.get('status', '').strip()
    invalid_filters = False

    if from_date and to_date and from_date > to_date:
        invalid_filters = True

    attendance_queryset = Attendance.objects.select_related('employee')
    visits_queryset = ClientVisit.objects.select_related('employee')

    employee_name = 'All'
    if employee_id:
        employee = employees.filter(pk=employee_id).first()
        if employee is not None:
            employee_name = employee.name
            attendance_queryset = attendance_queryset.filter(employee_id=employee_id)
            visits_queryset = visits_queryset.filter(employee_id=employee_id)

    if from_date:
        attendance_queryset = attendance_queryset.filter(date__gte=from_date)
        visits_queryset = visits_queryset.filter(visit_date__gte=from_date)

    if to_date:
        attendance_queryset = attendance_queryset.filter(date__lte=to_date)
        visits_queryset = visits_queryset.filter(visit_date__lte=to_date)

    if visit_status:
        visits_queryset = visits_queryset.filter(status=visit_status)

    attendance_records = attendance_queryset.order_by('-date', '-check_in')
    visits = visits_queryset.order_by('-visit_date', '-created_at')

    attendance_aggregates = attendance_queryset.aggregate(
        total=Count('id'),
        total_present=Count('id', filter=Q(status=Attendance.Status.PRESENT)),
    )
    visit_aggregates = visits_queryset.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status=ClientVisit.Status.PENDING)),
        completed=Count('id', filter=Q(status=ClientVisit.Status.COMPLETED)),
    )

    generated_at = timezone.localtime(timezone.now())
    generated_by = request.user.get_full_name() or request.user.username or 'System'

    return {
        'employees': employees,
        'from_date': from_date,
        'to_date': to_date,
        'employee_id': employee_id,
        'employee_name': employee_name,
        'visit_status': visit_status,
        'attendance_records': attendance_records,
        'visits': visits,
        'generated_date': generated_at.strftime('%Y-%m-%d'),
        'generated_time': generated_at.strftime('%H:%M:%S'),
        'generated_at': generated_at.strftime('%Y-%m-%d %H:%M:%S'),
        'generated_by': generated_by,
        'total_attendance_records': attendance_aggregates.get('total', 0),
        'total_present': attendance_aggregates.get('total_present', 0),
        'total_client_visits': visit_aggregates.get('total', 0),
        'pending_visits': visit_aggregates.get('pending', 0),
        'completed_visits': visit_aggregates.get('completed', 0),
        'invalid_filters': invalid_filters,
    }


@login_required(login_url='login')
def report_dashboard(request):
    context = _get_report_context(request)
    if context.get('invalid_filters'):
        messages.error(request, 'The selected date range is invalid. Please choose an end date that is on or after the start date.')
    return render(request, 'reports/dashboard.html', context)


@login_required(login_url='login')
def send_visit_reminders(request):
    today = timezone.localdate()
    reminder_date = today + timedelta(days=1)
    visits = ClientVisit.objects.select_related('employee').filter(visit_date=reminder_date)

    sent_count = 0
    for visit in visits:
        employee = visit.employee
        if not employee or not employee.email:
            continue
        send_mail(
            subject='Client visit tomorrow',
            message=(
                f"Client: {visit.client_name}\n"
                f"Location: {visit.location}\n"
                f"Time: {visit.visit_date}\n"
                f"Employee: {employee.name}\n"
            ),
            from_email=None,
            recipient_list=[employee.email],
            fail_silently=True,
        )
        sent_count += 1

    messages.success(request, f'Reminder emails sent for {sent_count} upcoming visit(s).')
    return redirect('reports:dashboard')


@login_required(login_url='login')
def download_pdf(request):
    context = _get_report_context(request)
    employee = request.user.employee if hasattr(request.user, 'employee') else None
    ActivityLog.objects.create(
        employee=employee,
        activity_type=ActivityLog.ActivityType.REPORT_GENERATED,
        title="Report Generated",
        description="A PDF report was generated.",
    )
    return build_pdf_response(context)


@login_required(login_url='login')
def download_excel(request):
    context = _get_report_context(request)
    employee = request.user.employee if hasattr(request.user, 'employee') else None
    ActivityLog.objects.create(
        employee=employee,
        activity_type=ActivityLog.ActivityType.REPORT_GENERATED,
        title="Report Generated",
        description="An Excel report was generated.",
    )
    return build_excel_response(context)


@login_required(login_url='login')
def download_csv(request):
    context = _get_report_context(request)
    employee = request.user.employee if hasattr(request.user, 'employee') else None
    ActivityLog.objects.create(
        employee=employee,
        activity_type=ActivityLog.ActivityType.REPORT_GENERATED,
        title="Report Generated",
        description="A CSV report was generated.",
    )
    return build_csv_response(context)
