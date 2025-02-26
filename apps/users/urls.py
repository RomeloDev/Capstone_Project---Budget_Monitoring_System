from django.urls import path
from . import views

urlpatterns = [
    path('', views.end_user_login, name='end_user_login'),
    path('signup/', views.end_user_signup, name='end_user_signup'),
    path('bms/admin/', views.admin_login, name='admin_login')
]