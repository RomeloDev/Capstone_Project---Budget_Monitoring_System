# bb_budget_monitoring_system/apps/admin_panel/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/export-excel/', views.export_admin_dashboard_excel, name='export_admin_dashboard_excel'),
    path('client_accounts/', views.client_accounts, name='client_accounts'),
    path('budget_allocation/', views.budget_allocation, name='budget_allocation'),
    path('departments-pr-request/', views.departments_pr_request, name='department_pr_request'),
    # path('departments-request/<int:request_id>/', views.handle_departments_request, name='handle_purchase_request'),
    # Purchase Request Management
    path('pr/<uuid:pr_id>/preview/', views.admin_preview_pr, name='admin_preview_pr'),
    path('pr/<uuid:request_id>/handle/', views.handle_departments_request, name='handle_purchase_request'),
    path('pr/export-excel/', views.export_pr_requests_excel, name='export_pr_requests_excel'),
    path('institutional-funds/', views.institutional_funds, name='institutional_funds'),
    path('admin_logout/', views.admin_logout, name='admin_logout'),
    path('registration/', views.register_account, name='register_account'),
    path('audit_trail/', views.audit_trail, name='audit_trail'),
    path('budget_realignment/', views.budget_re_alignment, name='budget_realignment'),
    path('handle_re_alignment_request/<int:pk>/', views.handle_re_alignment_request_action, name='handle_re_alignment_request_action'),
    path('pre_request_page/', views.pre_request_page, name='pre_request_page'),
    path('pre/<int:pk>/', views.admin_preview_pre, name='admin_preview_pre'),
    # path('pre/<int:pk>/action/', views.admin_handle_pre_action, name='admin_handle_pre_action'),
    path('preview_purchase_request/<int:pk>/', views.preview_purchase_request, name='preview_purchase_request'),

    # Activity Design Management
    path('ad/', views.departments_ad_request, name='departments_ad_request'),
    path('ad/<uuid:ad_id>/preview/', views.admin_preview_ad, name='admin_preview_ad'),
    path('ad/<uuid:pk>/handle/', views.handle_activity_design_request, name='handle_activity_design_request'),
    path('ad/<uuid:ad_id>/upload-signed-copy/', views.admin_upload_ad_signed_copy, name='admin_upload_ad_signed_copy'),
    path('ad/export-excel/', views.export_ad_requests_excel, name='export_ad_requests_excel'),

    # Legacy AD URLs (keep for backwards compatibility)
    path('department_activity_design/', views.departments_ad_request, name='department_activity_design'),
    path('department_ad_request/', views.departments_ad_request, name='department_ad_request'),
    path('handle_activity_design/<int:pk>/', views.handle_activity_design_request, name='handle_activity_design_request_legacy'),
    path('admin-preview-activity-design/<int:pk>/', views.admin_preview_activity_design, name='admin_preview_activity_design'),

    path('pre_budget_realignment/', views.pre_budget_realignment_admin, name='pre_budget_realignment_admin'),
    path('pre_budget_realignment/<int:pk>/action/', views.handle_pre_realignment_admin_action, name='handle_pre_realignment_admin_action'),
    path('download-document/<int:document_id>/', views.download_document, name='download_document'),
    path('export-budget-excel/<int:budget_id>/', views.export_budget_excel, name='export_budget_excel'),
    path('bulk-export-budgets/', views.bulk_export_budgets, name='bulk_export_budgets'),
    path('export-allocation-excel/<int:allocation_id>/', views.export_allocation_excel, name='export_allocation_excel'),
    path('bulk-export-allocations/', views.bulk_export_allocations, name='bulk_export_allocations'),
    # Main PRE List Page
    path('pre/', views.admin_pre_list, name='admin_pre_list'),
    path('pre/<uuid:pre_id>/', views.admin_pre_detail, name='admin_pre_detail'),
    # Basic Approve/Reject Action (Form POST)
    path('pre/<uuid:pre_id>/action/', views.admin_handle_pre_action, name='admin_handle_pre_action'),
    # Advanced Approve with Comment (AJAX)
    path('pre/<uuid:pre_id>/approve/', views.admin_approve_pre_with_comment, name='admin_approve_pre'),
    # Advanced Reject with Reason (AJAX)
    path('pre/<uuid:pre_id>/reject/', views.admin_reject_pre_with_reason, name='admin_reject_pre'),
    # Update PRE Status
    path('pre/<uuid:pre_id>/update-status/', views.admin_update_pre_status, name='admin_update_pre_status'),
    # PDF Generation
    path('pre/<uuid:pre_id>/generate-pdf/', views.admin_generate_pre_pdf, name='admin_generate_pre_pdf'),
    # Upload Signed Copy
    path('pre/<uuid:pre_id>/upload-signed/', views.admin_upload_signed_copy, name='admin_upload_signed_copy'),
    path('pre/<uuid:pre_id>/upload-manual-pdf/', views.admin_upload_manual_pdf, name='admin_upload_manual_pdf'),
    # PRE Approved Document Upload
    path('pre/<uuid:pre_id>/upload-approved-doc/', views.admin_upload_approved_document, name='admin_upload_approved_document'),
    path('pre/<uuid:pre_id>/quick-approve-upload/', views.admin_quick_approve_with_upload, name='admin_quick_approve_upload'),
    # PR Signed Copy Upload
    path('pr/<uuid:pr_id>/upload-signed-copy/', views.admin_upload_pr_signed_copy, name='admin_upload_pr_signed_copy'),
    path('pr/<uuid:pr_id>/manual-pdf-upload/', views.admin_manual_pdf_upload, name='admin_manual_pdf_upload'),

    # User Management AJAX Endpoints
    path('users/create/', views.create_user_ajax, name='create_user_ajax'),
    path('users/<int:user_id>/details/', views.get_user_details_ajax, name='get_user_details_ajax'),
    path('users/<int:user_id>/edit/', views.edit_user_ajax, name='edit_user_ajax'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status_ajax, name='toggle_user_status_ajax'),
    path('users/<int:user_id>/delete/', views.delete_user_ajax, name='delete_user_ajax'),
    path('users/bulk-action/', views.bulk_user_action_ajax, name='bulk_user_action_ajax'),
    path('users/export-excel/', views.export_users_excel, name='export_users_excel'),

    # Archive Management
    path('archive/', views.archive_center, name='archive_center'),
    path('archive/fiscal-year/<str:fiscal_year>/archive/', views.archive_fiscal_year_view, name='archive_fiscal_year'),
    path('archive/fiscal-year/<str:fiscal_year>/unarchive/', views.unarchive_fiscal_year_view, name='unarchive_fiscal_year'),
    path('archive/statistics/', views.archive_statistics_ajax, name='archive_statistics_ajax'),
]