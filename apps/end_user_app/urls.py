from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('view_budget/', views.view_budget, name='user_view_budget'),
     path('purchase_request', views.purchase_request, name='user_purchase_request'),
    path('settings/', views.settings, name='user_settings'),
    path('logout/', views.end_user_logout, name='logout'),
    path('purchase_request_form/', views.purchase_request_form, name='purchase_request_form'),
    path('add_purchase_item/', views.add_purchase_request_items, name='add_purchase_item'),
    path('remove-item/<int:item_id>/', views.remove_purchase_item, name='remove_purchase_item'),
    path('re_alignment/', views.re_alignment, name='re_alignment'),
    path('department_pre/', views.department_pre_form, name='department_pre_form'),
    path('department_pre_page/', views.department_pre_page, name='department_pre_page'),
    path('preview_pre/<int:pk>/', views.preview_pre, name='preview_pre'),
]