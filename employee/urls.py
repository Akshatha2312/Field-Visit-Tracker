from django.urls import path

from .views import (
    employee_create_view,
    employee_delete_view,
    employee_detail_view,
    employee_edit_view,
    employee_list_view,
    profile_view,
)

urlpatterns = [
    path('', profile_view, name='profile'),
    path('list/', employee_list_view, name='list'),
    path('add/', employee_create_view, name='create'),
    path('<int:pk>/', employee_detail_view, name='detail'),
    path('<int:pk>/edit/', employee_edit_view, name='edit'),
    path('<int:pk>/delete/', employee_delete_view, name='delete'),
]
