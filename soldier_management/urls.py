# soldier_management/urls.py
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from core.views import home_redirect, admin_dashboard, soldier_search_view


# تابع‌های redirect
def to_soldiers(request):
    return redirect('admin:core_soldier_changelist')


def to_leaves(request):
    return redirect('admin:core_leave_changelist')


urlpatterns = [
    path('', home_redirect),  # localhost:8000 → ادمین

    path('admin/dashboard/', admin_dashboard),
    path('admin/search/', soldier_search_view),

    path('admin/soldiers/', to_soldiers),
    path('admin/leaves/', to_leaves),

    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
