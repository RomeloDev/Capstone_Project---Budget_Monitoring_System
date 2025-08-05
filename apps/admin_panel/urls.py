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
    path('registration/', views.register_account, name='register_account'),
    path('audit_trail', views.audit_trail, name='audit_trail'),
    path('budget_realignment', views.budget_re_alignment, name='budget_realignment'),
    path('handle_re_alignment_request/<int:pk>/', views.handle_re_alignment_request_action, name='handle_re_alignment_request_action'),
    path('pre_request_page', views.pre_request_page, name='pre_request_page'),
]