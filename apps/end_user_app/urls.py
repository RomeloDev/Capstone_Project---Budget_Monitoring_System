# bb_budget_monitoring_system/apps/end_user_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('view_budget/', views.view_budget, name='user_view_budget'),
    path('pr-ad-request/', views.purchase_request, name='user_purchase_request'),
    path('settings/', views.user_settings_page, name='user_settings'),
    path('logout/', views.end_user_logout, name='logout'),
    path('pr-ad-request/purchase_request_form/', views.purchase_request_form, name='purchase_request_form'),
    path('pr-ad-request/purchase_request_upload_form/', views.purchase_request_upload, name='purchase_request_upload'),
    path('get-pre-line-items/', views.get_pre_line_items, name='get_pre_line_items'),
    path('add_purchase_item/', views.add_purchase_request_items, name='add_purchase_item'),
    path('remove-item/<int:item_id>/', views.remove_purchase_item, name='remove_purchase_item'),
    path('preview_purchase_request/<int:pk>/', views.preview_purchase_request, name='end_user_preview_purchase_request'),
    path('re_alignment/', views.re_alignment, name='re_alignment'),
    path('department_pre/<int:pk>/', views.department_pre_form, name='department_pre_form'),
    path('department_pre_page/', views.department_pre_page, name='department_pre_page'),
    path('pre/preview_pre', views.preview_pre, name='preview_pre'),
    path('pr-ad-request/activity_design_form/', views.activity_design_form, name='activity_design_form'),
    path('preview_activity_design/<int:pk>', views.preview_activity_design, name='preview_activity_design'),
    path('load_source_of_fund/', views.load_source_of_fund, name='load_source_of_fund'),
    path('view_budget/budget_details/<int:budget_id>/', views.budget_details, name='budget_details'),
    path('pre_budget_realignment/', views.pre_budget_realignment, name='pre_budget_realignment'),
    path('realignment_history/', views.realignment_history, name='realignment_history'),
    path('download_activity_design/<int:pk>/', views.download_activity_design_word, name='download_activity_design_word'),
    path('inspect_excel_template/', views.inspect_excel_template, name='inspect_excel_template'), 
    path('download_pre_excel/<int:pk>/', views.download_pre_excel, name='download_pre_excel'),
    path('pre/download_pre_template/', views.download_pre_template, name='download_pre_template'),
    path('pre/upload_pre/<int:allocation_id>/', views.upload_pre, name='upload_pre'),
    path('pre/view/<uuid:pre_id>/', views.view_pre_detail, name='view_pre_detail'),
    path('pr/preview/<uuid:pr_id>/', views.preview_submitted_pr, name='preview_submitted_pr'),
]