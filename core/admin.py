from django.contrib import admin
from .models import (
    SoldierRole,
    ShiftConfig,
    PostType,
    Soldier,
    Leave,
    DailySchedule,
    PostAssignment,
)

@admin.register(SoldierRole)
class SoldierRoleAdmin(admin.ModelAdmin):
    # فیلد description با priority جایگزین شد
    list_display = ("name", "priority")
    search_fields = ("name",)

@admin.register(ShiftConfig)
class ShiftConfigAdmin(admin.ModelAdmin):
    # 'is_active' removed
    list_display = ("name", "start_time", "end_time", "order")
    ordering = ("order",)

@admin.register(PostType)
class PostTypeAdmin(admin.ModelAdmin):
    # فیلد description با required_count جایگزین شد
    list_display = ("name", "required_count")
    search_fields = ("name",)

@admin.register(Soldier)
class SoldierAdmin(admin.ModelAdmin):
    # Removed 'full_name' (from ordering), 'health_type', 'has_driving_license'
    # Assuming first_name and last_name exist based on standard models
    list_display = ("first_name", "last_name", "national_code", "role", "is_active")
    list_filter = ("is_active", "role")
    search_fields = ("first_name", "last_name", "national_code")
    # ordering by standard fields instead of full_name
    ordering = ("last_name", "first_name")

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    # Removed 'end_date'
    list_display = ("soldier", "leave_type", "start_date", "days")
    list_filter = ("leave_type",)
    ordering = ("-start_date",)

@admin.register(DailySchedule)
class DailyScheduleAdmin(admin.ModelAdmin):
    list_display = ("date", "is_finalized")
    ordering = ("-date",)

@admin.register(PostAssignment)
class PostAssignmentAdmin(admin.ModelAdmin):
    # Removed 'is_override'
    list_display = ("schedule", "post_type", "shift", "soldier")
    list_filter = ("post_type", "shift")
    ordering = ("-schedule__date",)
