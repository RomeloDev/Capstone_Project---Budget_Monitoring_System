from django.urls import path
from . import views

urlpatterns = [
    path('dashboard', views.admin_dashboard, name='admin_dashboard'),
    path('client_accounts/', views.client_accounts, name='client_accounts'),
    path('budget_allocation/', views.budget_allocation, name='budget_allocation'),
    path('departments-request/', views.departments_request, name='department_request'),
    path('departments-request/<int:request_id>/', views.handle_departments_request, name='handle_purchase_request'),
    path('institutional-funds/', views.institutional_funds, name='institutional_funds'),
    path('admin_logout/', views.admin_logout, name='admin_logout'),
]