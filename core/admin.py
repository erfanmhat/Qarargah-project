from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from jalali_date.admin import ModelAdminJalaliMixin

from core.models import (
    Soldier, Leave,
    ServiceLocation, HealthStatus, ServiceStatus, Expertise,
    ServiceReductionType, SystemSetting, SoldierServiceReduction,
    MilitaryRankRef, ExtraServiceType, SoldierExtraServiceLog, DocumentTemplateInput, DocumentTemplate
)
from core.forms import SoldierForm, LeaveForm
from core.templatetags.jalali import to_jalali


# ==================== Inline ها ====================

class SoldierServiceReductionInline(admin.TabularInline):
    model = SoldierServiceReduction
    extra = 0
    autocomplete_fields = ('reduction_type',)


class SoldierExtraServiceLogInline(admin.TabularInline):
    model = SoldierExtraServiceLog
    extra = 0
    autocomplete_fields = ('extra_type',)


# ==================== Soldier Admin ====================

@admin.register(Soldier)
class SoldierAdmin(ModelAdminJalaliMixin, ImportExportModelAdmin):
    form = SoldierForm

    list_display = (
        'full_name', 'national_code', 'dossier_code',
        'get_dispatch_type_display',
        'jalali_service_start', 'jalali_service_end',
        'service_status',
        'military_rank', 'military_rank_ref',
    )

    search_fields = (
        'full_name',
        'national_code',
        'dossier_code',
        'father_name',
        'birth_place',
        'issue_place',
        'phone_personal',
        'personal_mobile_phone',
        'military_mobile_phone',
    )

    list_filter = (
        'dispatch_type', 'service_status', 'health_status',
        'current_location', 'expertises',
        'marital_status', 'blood_group',
        'has_driving_license',
    )

    readonly_fields = ('jalali_service_end',)

    autocomplete_fields = (
        'current_location',
        'service_status',
        'health_status',
        'military_rank_ref',
        'extra_service_type',
    )

    filter_horizontal = ('expertises',)

    inlines = (SoldierServiceReductionInline, SoldierExtraServiceLogInline)

    fieldsets = (
        ("اطلاعات هویتی", {
            'fields': (
                ('full_name', 'father_name'),
                ('national_code', 'dossier_code'),
                ('birth_date', 'birth_place'),
                ('issue_place', 'personal_photo'),
            )
        }),
        ("درجه و وضعیت خانوادگی", {
            'fields': (
                ('military_rank_ref', 'military_rank'),
                ('marital_status', 'children_count'),
            )
        }),
        ("ویژگی‌های ظاهری و پزشکی", {
            'fields': (
                ('height_cm', 'weight_kg'),
                ('eye_color', 'blood_group'),
                'underlying_disease',
                'drug_allergy',
                'used_medications',
            )
        }),
        ("اطلاعات تماس", {
            'fields': (
                ('phone_personal', 'personal_mobile_phone'),
                ('military_mobile_phone', 'phone_parent'),
                ('father_home_phone', 'personal_home_phone'),
                ('phone_home', 'phone_work'),
            )
        }),
        ("آدرس‌ها", {
            'fields': (
                'father_home_address',
                'personal_home_address',
                'home_address',
                'postal_code',
            )
        }),
        ("تحصیلات و مهارت‌ها", {
            'fields': (
                ('education_level', 'education_field'),
                ('has_driving_license', 'driving_license_type'),
                'expertises',
                'completed_courses',
            )
        }),
        ("اطلاعات خدمت", {
            'fields': (
                ('dispatch_type', 'guard_code'),
                ('service_start_date', 'arrival_date'),
                ('current_location', 'service_status'),
                'health_status',
                ('extra_service_days', 'extra_service_type'),
            )
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


# ==================== Leave Admin ====================

@admin.register(Leave)
class LeaveAdmin(ModelAdminJalaliMixin, ImportExportModelAdmin):
    form = LeaveForm
    list_display = ('soldier', 'get_leave_type_display', 'jalali_start', 'days')
    list_filter = ('leave_type', 'start_date')
    search_fields = ('soldier__full_name', 'soldier__national_code')
    date_hierarchy = 'start_date'

    fieldsets = (
        ("اطلاعات اصلی مرخصی", {
            'fields': ('soldier', 'leave_type', 'start_date', 'days')
        }),
        ("توضیحات", {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def jalali_start(self, obj):
        return to_jalali(obj.start_date, "%Y/%m/%d")

    jalali_start.short_description = "تاریخ رفت"


# ==================== ثبت بقیه مدل‌ها ====================

@admin.register(MilitaryRankRef)
class MilitaryRankRefAdmin(admin.ModelAdmin):
    list_display = ('title', 'code')
    search_fields = ('title', 'code')
    ordering = ('code',)

    def response_add(self, request, obj, post_url_continue=None):
        return super().response_add(request, obj, post_url_continue)


@admin.register(ExtraServiceType)
class ExtraServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('title', 'default_days')
    search_fields = ('title',)
    ordering = ('title',)

    def response_add(self, request, obj, post_url_continue=None):
        return super().response_add(request, obj, post_url_continue)


@admin.register(SoldierExtraServiceLog)
class SoldierExtraServiceLogAdmin(ModelAdminJalaliMixin, ImportExportModelAdmin):
    list_display = ('soldier', 'extra_type', 'days', 'created_at')
    search_fields = ('soldier__full_name', 'soldier__national_code', 'extra_type__title')
    list_filter = ('extra_type',)


@admin.register(ServiceLocation)
class ServiceLocationAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name',)


@admin.register(ServiceStatus)
class ServiceStatusAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    list_display = ('title', 'is_active_service')


@admin.register(HealthStatus)
class HealthStatusAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    list_display = ('title',)


@admin.register(ServiceReductionType)
class ServiceReductionTypeAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    list_display = ('title',)


class DocumentTemplateInputInline(admin.TabularInline):
    model = DocumentTemplateInput
    extra = 0
    fields = ("order", "key", "label", "input_type", "required", "default_value", "placeholder", "choices_text")
    ordering = ("order",)


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "filename", "is_active", "order")
    list_filter = ("is_active",)
    search_fields = ("title", "filename")
    ordering = ("order",)
    inlines = (DocumentTemplateInputInline,)


admin.site.register(Expertise)
admin.site.register(SystemSetting)
admin.site.register(SoldierServiceReduction)
