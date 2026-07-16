from django.urls import path

from .views import analytics_data, dashboard, home, login_view, logout_view

urlpatterns = [
    path('', home, name='home'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('dashboard/analytics-data/', analytics_data, name='analytics_data'),
]
