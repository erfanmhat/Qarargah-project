# core/urls_panel.py
from django.urls import path
from .views import (
    panel_login, panel_logout, panel_dashboard,
    panel_soldiers, panel_leaves, panel_search,
    panel_soldier_detail, panel_soldier_delete, panel_leave_delete,
    health_check, export_soldiers_excel, export_leaves_excel,
    panel_reports, seed_data, panel_backup_restore, panel_settings,
    export_database, import_database, soldier_profile_pdf,
    soldier_leaves_pdf, import_excel, import_excel_confirm
)

urlpatterns = [
    path('login/', panel_login, name='panel_login'),
    path('logout/', panel_logout, name='panel_logout'),
    path('', panel_dashboard, name='panel_dashboard'),
    path('soldiers/', panel_soldiers, name='panel_soldiers'),
    path('soldier/<int:soldier_id>/', panel_soldier_detail, name='panel_soldier_detail'),
    path('soldier/<int:soldier_id>/pdf/profile/', soldier_profile_pdf, name='soldier_profile_pdf'),
    path('soldier/<int:soldier_id>/pdf/leaves/', soldier_leaves_pdf, name='soldier_leaves_pdf'),
    path('soldier/<int:soldier_id>/delete/', panel_soldier_delete, name='panel_soldier_delete'),
    path('soldiers/export/', export_soldiers_excel, name='export_soldiers_excel'),
    path('leaves/', panel_leaves, name='panel_leaves'),
    path('leave/<int:leave_id>/delete/', panel_leave_delete, name='panel_leave_delete'),
    path('leaves/export/', export_leaves_excel, name='export_leaves_excel'),
    path('search/', panel_search, name='panel_search'),
    path('reports/', panel_reports, name='panel_reports'),
    path('settings/', panel_settings, name='panel_settings'),
    path('backup-restore/', panel_backup_restore, name='panel_backup_restore'),
    path('backup-restore/export/', export_database, name='export_database'),
    path('backup-restore/import/', import_database, name='import_database'),
    path('seed/', seed_data, name='seed_data'),
    path("import/excel/", import_excel, name="import_excel"),
    path("import/excel/confirm/", import_excel_confirm, name="import_excel_confirm"),
    path('health/', health_check, name='health_check'),
]
