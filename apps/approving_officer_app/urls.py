from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='approving_officer_dashboard'),
    path('department_request/', views.department_request, name='cd_department_request'),
    path('settings/', views.settings, name='cd_settings'),
]