from django.urls import path
from . import views

urlpatterns = [
    path('', views.end_user_login, name='end_user_login'),
    path('signup/', views.end_user_signup, name='end_user_signup'),
    path('admin/', views.admin_login, name='admin_login'),

    # Password Reset URLs
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/sent/', views.password_reset_sent, name='password_reset_sent'),
    path('password-reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/complete/', views.password_reset_complete, name='password_reset_complete'),
]