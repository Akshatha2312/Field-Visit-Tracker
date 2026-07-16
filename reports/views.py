from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from attendance.models import Attendance
from employee.models import Employee
from visits.models import ClientVisit


@login_required(login_url='login')
def report_dashboard(request):
    employees = Employee.objects.order_by('name')

    from_date = request.GET.get('from_date', '').strip()
    to_date = request.GET.get('to_date', '').strip()
    employee_id = request.GET.get('employee', '').strip()
    visit_status = request.GET.get('status', '').strip()

    attendance_queryset = Attendance.objects.select_related('employee')
    visits_queryset = ClientVisit.objects.select_related('employee')

    if employee_id:
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

    context = {
        'employees': employees,
        'from_date': from_date,
        'to_date': to_date,
        'employee_id': employee_id,
        'visit_status': visit_status,
        'attendance_records': attendance_records,
        'visits': visits,
        'total_attendance_records': attendance_records.count(),
        'total_present': attendance_records.filter(status=Attendance.Status.PRESENT).count(),
        'total_client_visits': visits.count(),
        'pending_visits': visits.filter(status=ClientVisit.Status.PENDING).count(),
        'completed_visits': visits.filter(status=ClientVisit.Status.COMPLETED).count(),
    }
    return render(request, 'reports/dashboard.html', context)
