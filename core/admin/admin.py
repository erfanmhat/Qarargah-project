# core/admin/admin.py
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from core.models import *
from ..forms import SoldierForm, LeaveForm
from ..templatetags.jalali import to_jalali


class SoldierAdmin(ImportExportModelAdmin):
    form = SoldierForm
    list_display = (
        'full_name', 'national_code', 'dossier_code', 'dispatch_type', 'jalali_service_start', 'jalali_service_end')
    search_fields = ('first_name', 'last_name', 'national_code', 'dossier_code')
    list_filter = ('dispatch_type', 'health_status', 'service_status', 'current_location')
    readonly_fields = ('service_end_date',)

    def jalali_service_start(self, obj):
        return to_jalali(obj.service_start_date, "%Y/%m/%d")

    jalali_service_start.short_description = 'شروع خدمت'

    def jalali_service_end(self, obj):
        return to_jalali(obj.service_end_date(), "%Y/%m/%d")

    jalali_service_end.short_description = 'پایان خدمت'


class LeaveAdmin(ImportExportModelAdmin):
    form = LeaveForm
    list_display = ('soldier', 'get_leave_type_display', 'jalali_start', 'jalali_end', 'days', 'is_approved')
    list_filter = ('leave_type', 'is_approved')

    def jalali_start(self, obj):
        return to_jalali(obj.start_date, "%Y/%m/%d")

    jalali_start.short_description = 'از تاریخ'

    def jalali_end(self, obj):
        return to_jalali(obj.end_date, "%Y/%m/%d")

    jalali_end.short_description = 'تا تاریخ'


# ثبت مجدد همه ادمین‌ها با فرم شمسی
admin.site.unregister(Soldier)
admin.site.unregister(Leave)
admin.site.register(Soldier, SoldierAdmin)
admin.site.register(Leave, LeaveAdmin)

# بقیه مدل‌ها بدون تغییر
admin.site.register(ServiceLocation)
admin.site.register(HealthStatus)
admin.site.register(ServiceStatus)
admin.site.register(Expertise)
admin.site.register(ServiceReductionType)
admin.site.register(SystemSetting)
