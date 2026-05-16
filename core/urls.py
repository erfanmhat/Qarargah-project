from django.urls import path
from .views import schedule, soldiers, leaves

app_name = 'core'

urlpatterns = [
    # ===================
    # Schedule URLs
    # ===================
    # صفحه اصلی برنامه نگهبانی
    path('', schedule.schedule_index, name='schedule_index'),
    # نمایش برنامه یک روز خاص
    path('schedule/<str:date>/', schedule.schedule_day, name='schedule_day'),
    # ایجاد برنامه جدید
    path('schedule/generate/', schedule.schedule_generate, name='schedule_generate'),
    # نهایی کردن برنامه
    path('schedule/<int:schedule_id>/finalize/', schedule.schedule_finalize, name='schedule_finalize'),
    # خارج کردن برنامه از حالت نهایی
    path('schedule/<int:schedule_id>/unfinalize/', schedule.schedule_unfinalize, name='schedule_unfinalize'),
    # API endpoints for AJAX calls
    # پیشنهاد سرباز برای یک پست
    path('ajax/suggest-for-post/', schedule.suggest_for_post, name='suggest_for_post'),
    # انتساب یک سرباز به پست
    path('ajax/assign-soldier/', schedule.assign_soldier, name='assign_soldier'),
    # حذف انتساب
    path('ajax/remove-assignment/', schedule.remove_assignment, name='remove_assignment'),


    # ===================
    # Soldiers URLs
    # ===================
    # لیست سربازها
    path('soldiers/', soldiers.soldier_list, name='soldier_list'),
    # افزودن سرباز جدید
    path('soldiers/add/', soldiers.soldier_add, name='soldier_add'),
    # پروفایل سرباز
    path('soldiers/<int:soldier_id>/', soldiers.soldier_profile, name='soldier_profile'),
    # ویرایش اطلاعات سرباز
    path('soldiers/<int:soldier_id>/edit/', soldiers.soldier_edit, name='soldier_edit'),
    # حذف سرباز
    path('soldiers/<int:soldier_id>/delete/', soldiers.soldier_delete, name='soldier_delete'),


    # ===================
    # Leaves URLs
    # ===================
    # لیست مرخصی‌ها
    path('leaves/', leaves.leave_list, name='leave_list'),
    # افزودن مرخصی برای یک سرباز
    path('soldiers/<int:soldier_id>/leaves/add/', leaves.leave_add, name='leave_add'),
    # حذف مرخصی
    path('leaves/<int:leave_id>/delete/', leaves.leave_delete, name='leave_delete'),
]
