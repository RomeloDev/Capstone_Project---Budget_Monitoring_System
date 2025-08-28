from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='approving_officer_dashboard'),
    path('department_request/', views.department_request, name='cd_department_request'),
    path('pre/', views.department_pre_list, name='ao_department_pre_list'),
    path('pre/<int:pk>/', views.preview_pre, name='ao_preview_pre'),
    path('pre/<int:pk>/action/', views.handle_pre_action, name='ao_handle_pre_action'),
    path('settings/', views.settings, name='cd_settings'),
    path('logout/', views.approving_officer_logout, name='approving_officer_logout'),
    path('handle_request_action/<int:pk>/', views.handle_request_action, name='handle_request_action'),
    path('preview-purchase-request/<int:pk>/', views.preview_purchase_request, name='preview_purchase_request'),
]