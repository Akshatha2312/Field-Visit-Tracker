from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render

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
        'total_attendance_records': Attendance.objects.count(),
        'total_client_visits': ClientVisit.objects.count(),
        'pending_visits': ClientVisit.objects.filter(status=ClientVisit.Status.PENDING).count(),
        'completed_visits': ClientVisit.objects.filter(status=ClientVisit.Status.COMPLETED).count(),
    }
    return render(request, 'dashboard.html', {'stats': stats})
