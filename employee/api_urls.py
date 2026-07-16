from django.urls import path

from .views import EmployeeDetailView, EmployeeListView

urlpatterns = [
    path('', EmployeeListView.as_view(), name='employee-list'),
    path('<int:pk>/', EmployeeDetailView.as_view(), name='employee-detail'),
]
