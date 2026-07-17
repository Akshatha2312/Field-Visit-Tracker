from django.urls import path

from .views import mark_completed, visit_create, visit_delete, visit_detail, visit_edit, visit_list, visit_reports

urlpatterns = [
    path('', visit_list, name='list'),
    path('add/', visit_create, name='create'),
    path('reports/', visit_reports, name='reports'),
    path('<int:pk>/', visit_detail, name='detail'),
    path('<int:pk>/edit/', visit_edit, name='edit'),
    path('<int:pk>/delete/', visit_delete, name='delete'),
    path('<int:pk>/complete/', mark_completed, name='complete'),
]
