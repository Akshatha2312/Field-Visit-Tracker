from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required(login_url='login')
def report_dashboard(request):
    return render(request, 'reports/dashboard.html')
