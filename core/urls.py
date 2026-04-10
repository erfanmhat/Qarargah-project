from django.urls import path

from core.views_core import panel_settings, panel_reports, panel_dashboard, panel_logout, panel_login
from core.views_import_export_excel import export_leaves_excel, \
    export_soldiers_excel, soldier_leaves_excel, soldier_profile_excel
from core.views_soldier_leave import panel_search, panel_leave_delete, panel_leaves, panel_soldier_delete, \
    panel_soldiers, generate_document, panel_soldier_detail, document_templates_help

urlpatterns = [
    path('login/', panel_login, name='panel_login'),
    path('logout/', panel_logout, name='panel_logout'),
    path('', panel_dashboard, name='panel_dashboard'),
    path('soldiers/', panel_soldiers, name='panel_soldiers'),
    path('soldier/<int:soldier_id>/', panel_soldier_detail, name='panel_soldier_detail'),
    path("dashboard/soldier/<int:soldier_id>/excel/profile/", soldier_profile_excel, name="soldier_profile_excel"),
    path("dashboard/soldier/<int:soldier_id>/excel/leaves/", soldier_leaves_excel, name="soldier_leaves_excel"),
    path('soldier/<int:soldier_id>/delete/', panel_soldier_delete, name='panel_soldier_delete'),
    path('soldiers/export/', export_soldiers_excel, name='export_soldiers_excel'),
    path('leaves/', panel_leaves, name='panel_leaves'),
    path('leave/<int:leave_id>/delete/', panel_leave_delete, name='panel_leave_delete'),
    path('leaves/export/', export_leaves_excel, name='export_leaves_excel'),
    path('search/', panel_search, name='panel_search'),
    path('reports/', panel_reports, name='panel_reports'),
    path('settings/', panel_settings, name='panel_settings'),
    path("soldiers/<int:soldier_id>/documents/<int:template_id>/", generate_document, name="generate_document"),
    path("documents/help/", document_templates_help, name="document_templates_help"),
]
