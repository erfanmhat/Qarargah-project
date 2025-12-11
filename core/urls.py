# core/urls_panel.py
from django.urls import path
from .views import (
    panel_login, panel_logout, panel_dashboard,
    panel_soldiers, panel_leaves, panel_search,
    panel_soldier_detail, panel_soldier_delete, panel_leave_delete,
    health_check, export_soldiers_excel, export_leaves_excel,
    panel_reports, seed_data, panel_backup_restore, panel_settings,
    export_database, import_database, soldier_profile_pdf,
    soldier_leaves_pdf
)

urlpatterns = [
    path('dashboard/login/', panel_login, name='panel_login'),
    path('dashboard/logout/', panel_logout, name='panel_logout'),
    path('dashboard/', panel_dashboard, name='panel_dashboard'),
    path('dashboard/soldiers/', panel_soldiers, name='panel_soldiers'),
    path('dashboard/soldier/<int:soldier_id>/', panel_soldier_detail, name='panel_soldier_detail'),
    path('dashboard/soldier/<int:soldier_id>/pdf/profile/', soldier_profile_pdf, name='soldier_profile_pdf'),
    path('dashboard/soldier/<int:soldier_id>/pdf/leaves/', soldier_leaves_pdf, name='soldier_leaves_pdf'),
    path('dashboard/soldier/<int:soldier_id>/delete/', panel_soldier_delete, name='panel_soldier_delete'),
    path('dashboard/soldiers/export/', export_soldiers_excel, name='export_soldiers_excel'),
    path('dashboard/leaves/', panel_leaves, name='panel_leaves'),
    path('dashboard/leave/<int:leave_id>/delete/', panel_leave_delete, name='panel_leave_delete'),
    path('dashboard/leaves/export/', export_leaves_excel, name='export_leaves_excel'),
    path('dashboard/search/', panel_search, name='panel_search'),
    path('dashboard/reports/', panel_reports, name='panel_reports'),
    path('dashboard/settings/', panel_settings, name='panel_settings'),
    path('dashboard/backup-restore/', panel_backup_restore, name='panel_backup_restore'),
    path('dashboard/backup-restore/export/', export_database, name='export_database'),
    path('dashboard/backup-restore/import/', import_database, name='import_database'),
    path('dashboard/seed/', seed_data, name='seed_data'),
    path('health/', health_check, name='health_check'),
]