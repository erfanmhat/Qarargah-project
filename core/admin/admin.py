# core/admin/admin.py
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from core.models import (
    Leave, Soldier, ServiceLocation, HealthStatus,
    ServiceStatus, Expertise, ServiceReductionType, SystemSetting
)


@admin.register(ServiceLocation)
class ServiceLocationAdmin(ImportExportModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    search_fields = ('name',)


@admin.register(HealthStatus)
class HealthStatusAdmin(ImportExportModelAdmin):
    list_display = ('title', 'is_exempt_from_combat', 'created_at')
    search_fields = ('title',)


@admin.register(ServiceStatus)
class ServiceStatusAdmin(ImportExportModelAdmin):
    list_display = ('title', 'is_active_service', 'created_at')
    search_fields = ('title',)


@admin.register(Expertise)
class ExpertiseAdmin(ImportExportModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)


@admin.register(ServiceReductionType)
class ServiceReductionTypeAdmin(ImportExportModelAdmin):
    list_display = ('title', 'default_days', 'created_at')
    search_fields = ('title',)


@admin.register(SystemSetting)
class SystemSettingAdmin(ImportExportModelAdmin):
    list_display = ('key', 'value', 'description')
    search_fields = ('key', 'value')


@admin.register(Soldier)
class SoldierAdmin(ImportExportModelAdmin):
    list_display = ('full_name', 'national_code', 'dossier_code', 'dispatch_type', 'service_end_date')
    search_fields = ('first_name', 'last_name', 'national_code', 'dossier_code')
    list_filter = ('dispatch_type', 'health_status', 'service_status', 'current_location')
    readonly_fields = ('service_end_date',)


@admin.register(Leave)
class LeaveAdmin(ImportExportModelAdmin):
    list_display = ('soldier', 'get_leave_type_display', 'start_date', 'end_date', 'days', 'is_approved')
    list_filter = ('leave_type', 'is_approved')
    search_fields = ('soldier__first_name', 'soldier__last_name', 'soldier__national_code')
