from django.urls import path

from .views import employee_list_view, profile_view

urlpatterns = [
    path('', profile_view, name='profile'),
    path('list/', employee_list_view, name='list'),
]
