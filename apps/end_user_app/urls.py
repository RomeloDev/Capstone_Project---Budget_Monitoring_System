from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('view_budget/', views.view_budget, name='user_view_budget'),
     path('purchase_request', views.purchase_request, name='user_purchase_request'),
    path('settings/', views.settings, name='user_settings'),
    path('logout/', views.end_user_logout, name='logout'),
]