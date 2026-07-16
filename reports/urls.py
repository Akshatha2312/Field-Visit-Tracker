from django.urls import path

from .views import download_pdf, report_dashboard

urlpatterns = [
    path('', report_dashboard, name='dashboard'),
    path('download-pdf/', download_pdf, name='download_pdf'),
]
