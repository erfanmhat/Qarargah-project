from django.contrib import admin

from core.models.reference import ServiceLocation


@admin.register(ServiceLocation, HealthStatus, ServiceStatus, Expertise, ServiceReductionType, SystemSetting)
class ReferenceAdmin(ImportExportModelAdmin):
    list_display = [f.name for f in admin.ModelAdmin().get_list_display(None)]
    search_fields = ['title', 'name']


@admin.register(Soldier)
class SoldierAdmin(ImportExportModelAdmin):
    list_display = ('full_name', 'national_code', 'dossier_code', 'dispatch_type', 'service_end_date')
    search_fields = ('first_name', 'last_name', 'national_code', 'dossier_code')
    list_filter = ('dispatch_type', 'health_status', 'service_status', 'current_location')


@admin.register(Leave)
class LeaveAdmin(ImportExportModelAdmin):
    list_display = ('soldier', 'leave_type', 'start_date', 'end_date', 'days', 'is_approved')
    list_filter = ('leave_type', 'is_approved')
    search_fields = ('soldier__first_name', 'soldier__last_name', 'soldier__national_code')
