from django.urls import path

from .views import attendance_dashboard, attendance_history, check_in, check_out

urlpatterns = [
    path('', attendance_dashboard, name='dashboard'),
    path('check-in/', check_in, name='check_in'),
    path('check-out/', check_out, name='check_out'),
    path('history/', attendance_history, name='history'),
]
