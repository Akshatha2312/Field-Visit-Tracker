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
    today = timezone.localdate()
    current_month = today.month
    
    # Get all counts in one aggregation call
    employee_count = Employee.objects.count()
    
    # Use aggregates to get all dashboard stats efficiently
    attendance_aggs = Attendance.objects.aggregate(
        today_count=Count('id', filter=Q(date=today)),
        month_count=Count('id', filter=Q(date__month=current_month)),
        today_present=Count('id', filter=Q(date=today, status=Attendance.Status.PRESENT)),
    )
    
    visit_aggs = ClientVisit.objects.aggregate(
        today_count=Count('id', filter=Q(visit_date=today)),
        pending_count=Count('id', filter=Q(status=ClientVisit.Status.PENDING)),
        monthly_count=Count('id', filter=Q(visit_date__month=current_month)),
        completed_count=Count('id'),
        total_count=Count('id'),
    )
    
    # Calculate derived values
    total_visits = visit_aggs['total_count']
    completed_visits = visit_aggs['completed_count']
    
    stats = {
        'total_employees': employee_count,
        'todays_attendance': attendance_aggs['today_count'],
        'todays_client_visits': visit_aggs['today_count'],
        'pending_visits': visit_aggs['pending_count'],
        'monthly_visits': visit_aggs['monthly_count'],
        'average_attendance': round(
            attendance_aggs['month_count'] / max(employee_count, 1) * 100, 1
        ) if employee_count else 0,
        'completion_rate': round(
            completed_visits * 100 / max(total_visits, 1), 1
        ) if total_visits else 0,
        'employees_present_today': attendance_aggs['today_present'],
    }
    recent_activities = ActivityLog.objects.select_related('employee').order_by('-created_at')[:10]
    return render(request, 'dashboard.html', {'stats': stats, 'recent_activities': recent_activities})


@login_required(login_url='login')
def analytics_data(request):
    today = timezone.localdate()
    current_year = today.year
    current_month = today.month

    # Fetch all data once
    attendance_queryset = Attendance.objects.all()
    visits_queryset = ClientVisit.objects.all()

    # Get attendance status distribution
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

    # Get monthly visits data
    monthly_visits_data = (
        visits_queryset.filter(visit_date__year=current_year)
        .values('visit_date__month')
        .annotate(count=Count('id'))
    )
    monthly_visits_dict = {item['visit_date__month']: item['count'] for item in monthly_visits_data}
    
    monthly_labels = []
    monthly_values = []
    for month_index in range(1, 13):
        monthly_labels.append(month_name[month_index][:3])
        monthly_values.append(monthly_visits_dict.get(month_index, 0))

    # Get visit status distribution
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

    # Get top employees by visits
    employee_visits = (
        visits_queryset.values('employee__name')
        .annotate(
            total_visits=Count('id'),
            completed_visits=Count('id', filter=Q(status=ClientVisit.Status.COMPLETED)),
            pending_visits=Count('id', filter=Q(status=ClientVisit.Status.PENDING))
        )
        .order_by('-total_visits', 'employee__name')[:8]
    )
    employee_labels = [item['employee__name'] for item in employee_visits]
    employee_values = [item['total_visits'] for item in employee_visits]

    # Get weekly attendance data
    weekly_attendance = (
        attendance_queryset.filter(date__year=current_year, date__month=current_month)
        .values('date')
        .annotate(
            present=Count('id', filter=Q(status=Attendance.Status.PRESENT)),
            absent=Count('id', filter=Q(status=Attendance.Status.ABSENT))
        )
        .order_by('date')[:7]
    )

    weekly_labels = [item['date'].strftime('%a') for item in weekly_attendance]
    weekly_present = [item['present'] for item in weekly_attendance]
    weekly_absent = [item['absent'] for item in weekly_attendance]

    # Get employee reports with aggregation instead of looping through all employees
    employee_reports_data = (
        attendance_queryset.values('employee__id', 'employee__name')
        .annotate(
            total_days=Count('id'),
            present_days=Count('id', filter=Q(status=Attendance.Status.PRESENT)),
            absent_days=Count('id', filter=Q(status=Attendance.Status.ABSENT))
        )
        .order_by('employee__name')
    )
    
    # Create a map of employee stats for quick lookup
    employee_stats_map = {
        item['employee__id']: {
            'total_days': item['total_days'],
            'present_days': item['present_days'],
            'absent_days': item['absent_days'],
        }
        for item in employee_reports_data
    }
    
    # Get visit data per employee
    employee_visit_data = (
        visits_queryset.values('employee__id')
        .annotate(
            total_visits=Count('id'),
            completed_visits=Count('id', filter=Q(status=ClientVisit.Status.COMPLETED)),
            pending_visits=Count('id', filter=Q(status=ClientVisit.Status.PENDING))
        )
    )
    
    employee_visit_map = {
        item['employee__id']: {
            'total_visits': item['total_visits'],
            'completed_visits': item['completed_visits'],
            'pending_visits': item['pending_visits'],
        }
        for item in employee_visit_data
    }
    
    # Combine all employee data
    employee_reports = []
    employees = Employee.objects.values('id', 'name')
    for employee in employees:
        emp_id = employee['id']
        emp_name = employee['name']
        
        stats = employee_stats_map.get(emp_id, {'total_days': 0, 'present_days': 0, 'absent_days': 0})
        visits = employee_visit_map.get(emp_id, {'total_visits': 0, 'completed_visits': 0, 'pending_visits': 0})
        
        total_days = stats['total_days']
        attendance_percentage = round((stats['present_days'] / total_days * 100) if total_days else 0, 1)
        
        employee_reports.append({
            'id': emp_id,
            'name': emp_name,
            'total_visits': visits['total_visits'],
            'completed_visits': visits['completed_visits'],
            'pending_visits': visits['pending_visits'],
            'attendance_percentage': attendance_percentage,
            'present_days': stats['present_days'],
            'absent_days': stats['absent_days'],
        })

    # Calculate summary statistics efficiently
    # Use previously aggregated data instead of additional .count() calls
    total_visits = sum(visit['total_visits'] for visit in employee_visit_data) if employee_visit_data else 0
    total_completed = sum(visit['completed_visits'] for visit in employee_visit_data) if employee_visit_data else 0
    today_present = sum(stat['present_days'] for stat in employee_stats_map.values()) if employee_stats_map else 0
    
    # Get summary stats using a single aggregate query for visits
    summary_visits_aggs = visits_queryset.aggregate(
        today_visits=Count('id', filter=Q(visit_date=today)),
        monthly_visits=Count('id', filter=Q(visit_date__month=current_month)),
    )
    
    # Get summary stats using a single aggregate query for attendance
    summary_attendance_aggs = attendance_queryset.aggregate(
        month_count=Count('id', filter=Q(date__month=current_month)),
    )
    
    # Total employees is the number of unique employees with attendance data plus those without
    total_employees = len(employee_stats_map) or Employee.objects.count()
    
    summary = {
        'today_visits': summary_visits_aggs['today_visits'],
        'monthly_visits': summary_visits_aggs['monthly_visits'],
        'average_attendance': round(
            summary_attendance_aggs['month_count'] / max(total_employees, 1) * 100, 1
        ),
        'completion_rate': round(
            total_completed * 100 / max(total_visits, 1), 1
        ) if total_visits else 0,
        'employees_present_today': today_present,
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
