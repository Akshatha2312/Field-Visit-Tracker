from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from attendance.models import Attendance
from employee.models import Employee
from visits.models import ClientVisit


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
    }
    return render(request, 'dashboard.html', {'stats': stats})


@login_required(login_url='login')
def analytics_data(request):
    today = timezone.localdate()
    current_year = today.year

    attendance_status_data = (
        Attendance.objects.values('status').annotate(count=Count('id')).order_by('status')
    )
    attendance_labels = []
    attendance_values = []
    for item in attendance_status_data:
        attendance_labels.append(item['status'])
        attendance_values.append(item['count'])

    monthly_visits = (
        ClientVisit.objects.filter(visit_date__year=current_year)
        .values('visit_date__month')
        .annotate(count=Count('id'))
        .order_by('visit_date__month')
    )
    month_names = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ]
    monthly_labels = []
    monthly_values = []
    for month_index in range(1, 13):
        month_entry = next((item for item in monthly_visits if item['visit_date__month'] == month_index), None)
        monthly_labels.append(month_names[month_index - 1])
        monthly_values.append(month_entry['count'] if month_entry else 0)

    visit_status_data = (
        ClientVisit.objects.values('status').annotate(count=Count('id')).order_by('status')
    )
    visit_status_labels = []
    visit_status_values = []
    for item in visit_status_data:
        visit_status_labels.append(item['status'])
        visit_status_values.append(item['count'])

    employee_visits = (
        ClientVisit.objects.values('employee__name').annotate(count=Count('id')).order_by('-count', 'employee__name')
    )
    employee_labels = [item['employee__name'] for item in employee_visits]
    employee_values = [item['count'] for item in employee_visits]

    return JsonResponse({
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
    })
