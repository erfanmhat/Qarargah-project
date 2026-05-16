from django.contrib import admin

from .models import (
    DailySchedule,
    Leave,
    PostAssignment,
    PostType,
    ShiftConfig,
    Soldier,
    SoldierRole,
)


@admin.register(SoldierRole)
class SoldierRoleAdmin(admin.ModelAdmin):
    list_display = ("title", "order")
    ordering = ("order",)


@admin.register(ShiftConfig)
class ShiftConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "start_time", "end_time", "order", "is_active")
    ordering = ("order",)


@admin.register(PostType)
class PostTypeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "soldiers_per_shift",
        "shift_count",
        "is_shift_based",
        "is_active",
        "order",
    )
    ordering = ("order",)


@admin.register(Soldier)
class SoldierAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "national_code",
        "health_type",
        "role",
        "has_driving_license",
        "is_active",
    )
    list_filter = ("health_type", "is_active", "role")
    search_fields = ("full_name", "national_code")
    ordering = ("full_name",)


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ("soldier", "leave_type", "start_date", "end_date", "days")
    list_filter = ("leave_type",)
    search_fields = ("soldier__full_name",)
    ordering = ("-start_date",)


@admin.register(DailySchedule)
class DailyScheduleAdmin(admin.ModelAdmin):
    list_display = ("date", "is_finalized")
    ordering = ("-date",)


@admin.register(PostAssignment)
class PostAssignmentAdmin(admin.ModelAdmin):
    list_display = ("schedule", "post_type", "shift", "soldier", "is_override")
    list_filter = ("post_type", "is_override")
    search_fields = ("soldier__full_name",)
    ordering = ("-schedule__date",)