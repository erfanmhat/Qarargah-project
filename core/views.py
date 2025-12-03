from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.admin.sites import AdminSite
from django.shortcuts import render, redirect


def home_redirect(request):
    return redirect('/admin/')


@staff_member_required
def admin_dashboard(request):
    # این خط همه context لازم ادمین رو می‌ده (از جمله log_entries و admin_log)
    admin_site = AdminSite()
    context = admin_site.each_context(request)

    # عنوان صفحه رو عوض می‌کنیم
    context['title'] = 'داشبورد مدیریت سامانه سربازان'

    # اگر خواستی recent actions هم نشون بده (اختیاری)
    # context['has_permission'] = True

    return render(request, 'admin/index.html', context)


@staff_member_required
def soldier_search_view(request):
    admin_site = AdminSite()
    context = admin_site.each_context(request)
    context['title'] = 'جستجو و فیلتر پیشرفته سربازان'
    return render(request, 'admin/soldier_search.html', context)
