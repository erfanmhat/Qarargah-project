from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import date

from core.models import Leave, Soldier
from core.forms import LeaveForm, LeaveSearchForm


def leave_list(request):
    """
    نمایش لیست مرخصی‌ها با قابلیت جستجو و فیلتر
    """
    leaves = Leave.objects.select_related('soldier').order_by('-start_date')
    
    # فرم جستجو
    search_form = LeaveSearchForm(request.GET or None)
    
    if search_form.is_valid():
        # فیلتر بر اساس سرباز
        soldier = search_form.cleaned_data.get('soldier')
        if soldier:
            leaves = leaves.filter(soldier=soldier)
        
        # فیلتر بر اساس نوع مرخصی
        leave_type = search_form.cleaned_data.get('leave_type')
        if leave_type:
            leaves = leaves.filter(leave_type=leave_type)
        
        # فیلتر بر اساس بازه تاریخ
        start_date = search_form.cleaned_data.get('start_date')
        end_date = search_form.cleaned_data.get('end_date')
        if start_date:
            leaves = leaves.filter(start_date__gte=start_date)
        if end_date:
            leaves = leaves.filter(end_date__lte=end_date)
        
        # فیلتر مرخصی‌های فعال (در حال حاضر)
        active_only = search_form.cleaned_data.get('active_only')
        if active_only:
            today = date.today()
            leaves = leaves.filter(start_date__lte=today, end_date__gte=today)
    
    # صفحه‌بندی
    paginator = Paginator(leaves, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'total_count': leaves.count(),
    }
    
    return render(request, 'core/leaves/list.html', context)


def leave_detail(request, pk):
    """
    نمایش جزئیات یک مرخصی
    """
    leave = get_object_or_404(Leave.objects.select_related('soldier'), pk=pk)
    
    context = {
        'leave': leave,
    }
    
    return render(request, 'core/leaves/detail.html', context)


def leave_create(request):
    """
    ثبت مرخصی جدید
    """
    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            leave = form.save()
            messages.success(request, f'مرخصی برای {leave.soldier.full_name} با موفقیت ثبت شد.')
            return redirect('core:leave_detail', pk=leave.pk)
    else:
        # اگر soldier_id در query string باشد، پیش‌فرض کن
        soldier_id = request.GET.get('soldier')
        initial = {}
        if soldier_id:
            try:
                soldier = Soldier.objects.get(pk=soldier_id)
                initial['soldier'] = soldier
            except Soldier.DoesNotExist:
                pass
        
        form = LeaveForm(initial=initial)
    
    context = {
        'form': form,
        'title': 'ثبت مرخصی جدید',
        'submit_text': 'ثبت مرخصی',
    }
    
    return render(request, 'core/leaves/form.html', context)


def leave_update(request, pk):
    """
    ویرایش مرخصی
    """
    leave = get_object_or_404(Leave, pk=pk)
    
    if request.method == 'POST':
        form = LeaveForm(request.POST, instance=leave)
        if form.is_valid():
            leave = form.save()
            messages.success(request, 'مرخصی با موفقیت ویرایش شد.')
            return redirect('core:leave_detail', pk=leave.pk)
    else:
        form = LeaveForm(instance=leave)
    
    context = {
        'form': form,
        'leave': leave,
        'title': 'ویرایش مرخصی',
        'submit_text': 'ذخیره تغییرات',
    }
    
    return render(request, 'core/leaves/form.html', context)


def leave_delete(request, pk):
    """
    حذف مرخصی
    """
    leave = get_object_or_404(Leave.objects.select_related('soldier'), pk=pk)
    
    if request.method == 'POST':
        soldier_name = leave.soldier.full_name
        leave.delete#TODO fix this