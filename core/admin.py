# core/dashboard.py
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from jalali_date.admin import ModelAdminJalaliMixin
from core.models import *
from core.forms import SoldierForm, LeaveForm
from core.templatetags.jalali import to_jalali


@admin.register(Soldier)
class SoldierAdmin(ModelAdminJalaliMixin, ImportExportModelAdmin):
    form = SoldierForm
    list_display = ('full_name', 'national_code', 'dossier_code', 'get_dispatch_type_display',
                    'jalali_service_start', 'jalali_service_end', 'service_status')
    search_fields = ('first_name', 'last_name', 'national_code', 'dossier_code', 'phone_personal')
    list_filter = ('dispatch_type', 'service_status', 'health_status', 'current_location', 'expertises')
    readonly_fields = ('jalali_service_end',)

    fieldsets = (
        ("اطلاعات هویتی", {
            'fields': ('first_name', 'last_name', 'national_code', 'birth_date')
        }),
        ("اطلاعات خدمت", {
            'fields': ('dispatch_type', 'dossier_code', 'service_start_date', 'arrival_date',
                       'current_location', 'service_status', 'health_status', 'extra_service_days')
        }),
        ("اطلاعات تماس", {
            'fields': (('phone_personal', 'phone_parent'), ('phone_home', 'phone_work'), 'home_address', 'guard_code')
        }),
        ("تخصص‌ها", {
            'fields': ('expertises',),
        }),
        ("تاریخ پایان خدمت", {
            'fields': ('jalali_service_end',),
            'description': '<div class="help">این فیلد به صورت خودکار محاسبه می‌شود</div>'
        }),
    )

    def jalali_service_start(self, obj):
        return to_jalali(obj.service_start_date, "%Y/%m/%d") if obj.service_start_date else "—"

    jalali_service_start.short_description = "شروع خدمت"

    def jalali_service_end(self, obj):
        end = obj.service_end_date()
        return to_jalali(end, "%Y/%m/%d") if end else "—"

    jalali_service_end.short_description = "پایان خدمت (شمسی)"


@admin.register(Leave)
class LeaveAdmin(ModelAdminJalaliMixin, ImportExportModelAdmin):
    form = LeaveForm
    list_display = ('soldier', 'get_leave_type_display', 'jalali_start', 'jalali_end', 'days')
    list_filter = ('leave_type', 'start_date')
    search_fields = ('soldier__first_name', 'soldier__last_name', 'soldier__national_code')
    date_hierarchy = 'start_date'

    fieldsets = (
        ("اطلاعات اصلی مرخصی", {
            'fields': ('soldier', 'leave_type', 'start_date', 'end_date')
        }),
        ("توضیحات", {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def jalali_start(self, obj):
        return to_jalali(obj.start_date, "%Y/%m/%d")

    jalali_start.short_description = "تاریخ رفت"

    def jalali_end(self, obj):
        return to_jalali(obj.end_date, "%Y/%m/%d")

    jalali_end.short_description = "تاریخ برگشت"


# ثبت بقیه مدل‌ها با نام فارسی
admin.site.register(ServiceLocation)
admin.site.register(HealthStatus)
admin.site.register(ServiceStatus)
admin.site.register(Expertise)
admin.site.register(ServiceReductionType)
admin.site.register(SystemSetting)
admin.site.register(SoldierServiceReduction)

# تنظیمات کلی ادمین
admin.site.index_template = 'dashboard/index.html'
