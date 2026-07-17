from calendar import month_name

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from attendance.models import Attendance
from employee.models import Employee
from visits.models import ClientVisit

from .models import ActivityLog


def home(request):
    return render(request, 'home.html')


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)
    else:
        form = AuthenticationForm(request)

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required(login_url='login')
def dashboard(request):
    stats = {
        'total_employees': Employee.objects.count(),
        'todays_attendance': Attendance.objects.filter(date=timezone.localdate()).count(),
        'todays_client_visits': ClientVisit.objects.filter(visit_date=timezone.localdate()).count(),
        'pending_visits': ClientVisit.objects.filter(status=ClientVisit.Status.PENDING).count(),
        'monthly_visits': ClientVisit.objects.filter(visit_date__month=timezone.localdate().month).count(),
        'average_attendance': round(
            Attendance.objects.filter(date__month=timezone.localdate().month).aggregate(avg=Count('id'))['avg'] / max(Employee.objects.count(), 1) * 100, 1
        ) if Employee.objects.count() else 0,
        'completion_rate': round(
            ClientVisit.objects.filter(status=ClientVisit.Status.COMPLETED).count() * 100 / max(ClientVisit.objects.count(), 1), 1
        ) if ClientVisit.objects.count() else 0,
        'employees_present_today': Attendance.objects.filter(date=timezone.localdate(), status=Attendance.Status.PRESENT).count(),
    }
    recent_activities = ActivityLog.objects.select_related('employee').order_by('-created_at')[:10]
    return render(request, 'dashboard.html', {'stats': stats, 'recent_activities': recent_activities})


@login_required(login_url='login')
def analytics_data(request):
    today = timezone.localdate()
    current_year = today.year
    current_month = today.month

    attendance_queryset = Attendance.objects.all()
    visits_queryset = ClientVisit.objects.select_related('employee')

    attendance_status_data = attendance_queryset.values('status').annotate(count=Count('id')).order_by('status')
    attendance_status_map = {
        Attendance.Status.PRESENT: 0,
        Attendance.Status.ABSENT: 0,
    }
    for item in attendance_status_data:
        if item['status'] in attendance_status_map:
            attendance_status_map[item['status']] = item['count']

    attendance_labels = [Attendance.Status.PRESENT, Attendance.Status.ABSENT]
    attendance_values = [attendance_status_map[Attendance.Status.PRESENT], attendance_status_map[Attendance.Status.ABSENT]]

    monthly_visits = (
        visits_queryset.filter(visit_date__year=current_year)
        .values('visit_date__month')
        .annotate(count=Count('id'))
        .order_by('visit_date__month')
    )
    monthly_labels = []
    monthly_values = []
    for month_index in range(1, 13):
        month_entry = next((item for item in monthly_visits if item['visit_date__month'] == month_index), None)
        monthly_labels.append(month_name[month_index][:3])
        monthly_values.append(month_entry['count'] if month_entry else 0)

    visit_status_data = visits_queryset.values('status').annotate(count=Count('id')).order_by('status')
    visit_status_map = {
        ClientVisit.Status.PENDING: 0,
        ClientVisit.Status.COMPLETED: 0,
    }
    for item in visit_status_data:
        if item['status'] in visit_status_map:
            visit_status_map[item['status']] = item['count']

    visit_status_labels = [ClientVisit.Status.PENDING, ClientVisit.Status.COMPLETED]
    visit_status_values = [visit_status_map[ClientVisit.Status.PENDING], visit_status_map[ClientVisit.Status.COMPLETED]]

    employee_visits = (
        visits_queryset.values('employee__name')
        .annotate(total_visits=Count('id'), completed_visits=Count('id', filter=Q(status=ClientVisit.Status.COMPLETED)), pending_visits=Count('id', filter=Q(status=ClientVisit.Status.PENDING)))
        .order_by('-total_visits', 'employee__name')[:8]
    )
    employee_labels = [item['employee__name'] for item in employee_visits]
    employee_values = [item['total_visits'] for item in employee_visits]

    weekly_attendance = (
        attendance_queryset.filter(date__year=current_year, date__month=current_month)
        .values('date')
        .annotate(present=Count('id', filter=Q(status=Attendance.Status.PRESENT)), absent=Count('id', filter=Q(status=Attendance.Status.ABSENT)))
        .order_by('date')[:7]
    )

    weekly_labels = [item['date'].strftime('%a') for item in weekly_attendance]
    weekly_present = [item['present'] for item in weekly_attendance]
    weekly_absent = [item['absent'] for item in weekly_attendance]

    employee_reports = []
    employees = Employee.objects.all()
    for employee in employees:
        employee_attendance = attendance_queryset.filter(employee=employee)
        total_days = employee_attendance.count()
        present_days = employee_attendance.filter(status=Attendance.Status.PRESENT).count()
        absent_days = employee_attendance.filter(status=Attendance.Status.ABSENT).count()
        attendance_percentage = round((present_days / total_days * 100) if total_days else 0, 1)
        visit_data = visits_queryset.filter(employee=employee)
        employee_reports.append({
            'id': employee.id,
            'name': employee.name,
            'total_visits': visit_data.count(),
            'completed_visits': visit_data.filter(status=ClientVisit.Status.COMPLETED).count(),
            'pending_visits': visit_data.filter(status=ClientVisit.Status.PENDING).count(),
            'attendance_percentage': attendance_percentage,
            'present_days': present_days,
            'absent_days': absent_days,
        })

    summary = {
        'today_visits': visits_queryset.filter(visit_date=today).count(),
        'monthly_visits': visits_queryset.filter(visit_date__month=current_month).count(),
        'average_attendance': round(
            attendance_queryset.filter(date__month=current_month).count() / max(Employee.objects.count(), 1) * 100, 1
        ),
        'completion_rate': round(
            visits_queryset.filter(status=ClientVisit.Status.COMPLETED).count() * 100 / max(visits_queryset.count(), 1), 1
        ) if visits_queryset.count() else 0,
        'employees_present_today': attendance_queryset.filter(date=today, status=Attendance.Status.PRESENT).count(),
    }

    return JsonResponse({
        'summary': summary,
        'attendance': {
            'labels': attendance_labels,
            'values': attendance_values,
        },
        'monthly_visits': {
            'labels': monthly_labels,
            'values': monthly_values,
        },
        'visit_status': {
            'labels': visit_status_labels,
            'values': visit_status_values,
        },
        'employee_visits': {
            'labels': employee_labels,
            'values': employee_values,
        },
        'weekly_attendance': {
            'labels': weekly_labels,
            'values': weekly_present,
            'absent_values': weekly_absent,
        },
        'employee_reports': employee_reports,
    })
