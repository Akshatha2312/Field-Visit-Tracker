from django.urls import path

from .views import AttendanceDetailView, AttendanceListView

urlpatterns = [
    path('', AttendanceListView.as_view(), name='attendance-list'),
    path('<int:pk>/', AttendanceDetailView.as_view(), name='attendance-detail'),
]
