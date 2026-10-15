from django.urls import path
from .views import soldiers, leaves, schedule, settings

app_name = "core"

urlpatterns = [
    # ==========================
    # Soldiers
    # ==========================
    path("soldiers/", soldiers.soldier_list, name="soldier_list"),
    path("soldiers/create/", soldiers.soldier_create, name="soldier_create"),
    path("soldiers/<int:pk>/", soldiers.soldier_detail, name="soldier_detail"),
    path("soldiers/<int:pk>/edit/", soldiers.soldier_update, name="soldier_update"),
    path("soldiers/<int:pk>/delete/", soldiers.soldier_delete, name="soldier_delete"),

    # ==========================
    # Leaves (اشتباه تایپی اصلاح شد)
    # ==========================
    path("leaves/", leaves.leave_list, name="leave_list"),
    path("leaves/create/", leaves.leave_create, name="leave_create"),
    path("leaves/<int:pk>/", leaves.leave_detail, name="leave_detail"),
    path("leaves/<int:pk>/edit/", leaves.leave_update, name="leave_update"),
    path("leaves/<int:pk>/delete/", leaves.leave_delete, name="leave_delete"),

    # ==========================
    # Schedule
    # ==========================
    path("schedule/", schedule.schedule_view, name="schedule_view"),
    path("schedule/generate/<int:schedule_id>/", schedule.generate_schedule, name="generate_schedule"),
    path("schedule/assign/", schedule.assign_soldier_to_post, name="assign_soldier_to_post"),
    path("schedule/override/<int:assignment_id>/", schedule.override_assignment, name="override_assignment"),

    # ==========================
    # Settings (Shift, Post, Role)
    # ==========================
    
    # Shifts
    path("settings/shifts/", settings.ShiftConfigListView.as_view(), name="shift_config_list"),
    path("settings/shifts/create/", settings.ShiftConfigCreateView.as_view(), name="shift_config_create"),
    path("settings/shifts/<int:pk>/edit/", settings.ShiftConfigUpdateView.as_view(), name="shift_config_update"),
    path("settings/shifts/<int:pk>/delete/", settings.ShiftConfigDeleteView.as_view(), name="shift_config_delete"),

    # Posts
    path("settings/posts/", settings.PostTypeListView.as_view(), name="post_type_list"),
    path("settings/posts/create/", settings.PostTypeCreateView.as_view(), name="post_type_create"),
    path("settings/posts/<int:pk>/edit/", settings.PostTypeUpdateView.as_view(), name="post_type_update"),
    path("settings/posts/<int:pk>/delete/", settings.PostTypeDeleteView.as_view(), name="post_type_delete"),
]
