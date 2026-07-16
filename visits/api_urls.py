from django.urls import path

from .views import ClientVisitDetailView, ClientVisitListView

urlpatterns = [
    path('', ClientVisitListView.as_view(), name='visit-list'),
    path('<int:pk>/', ClientVisitDetailView.as_view(), name='visit-detail'),
]
