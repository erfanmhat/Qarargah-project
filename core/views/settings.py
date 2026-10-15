# core/views/settings.py

from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from core.models import ShiftConfig, PostType

# ==========================================
# 1. تنظیمات شیفت‌ها (ShiftConfig)
# ==========================================

class ShiftConfigListView(LoginRequiredMixin, ListView):
    model = ShiftConfig
    template_name = 'settings/shifts/list.html'
    context_object_name = 'shifts'

class ShiftConfigCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ShiftConfig
    fields = '__all__'  # یا می‌توانید فرم اختصاصی از core.forms ایمپورت کنید
    template_name = 'settings/shifts/form.html'
    success_url = reverse_lazy('core:shift_config_list')
    success_message = "شیفت جدید با موفقیت ایجاد شد."

class ShiftConfigUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ShiftConfig
    fields = '__all__'
    template_name = 'settings/shifts/form.html'
    success_url = reverse_lazy('core:shift_config_list')
    success_message = "شیفت با موفقیت ویرایش شد."

class ShiftConfigDeleteView(LoginRequiredMixin, DeleteView):
    model = ShiftConfig
    template_name = 'settings/shifts/delete.html'
    success_url = reverse_lazy('core:shift_config_list')


# ==========================================
# 2. تنظیمات انواع پست‌ها (PostType)
# ==========================================

class PostTypeListView(LoginRequiredMixin, ListView):
    model = PostType
    template_name = 'settings/posts/list.html'
    context_object_name = 'posts'

class PostTypeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = PostType
    fields = '__all__'
    template_name = 'settings/posts/form.html'
    success_url = reverse_lazy('core:post_type_list')
    success_message = "پست جدید با موفقیت ایجاد شد."

class PostTypeUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = PostType
    fields = '__all__'
    template_name = 'settings/posts/form.html'
    success_url = reverse_lazy('core:post_type_list')
    success_message = "پست با موفقیت ویرایش شد."

class PostTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = PostType
    template_name = 'settings/posts/delete.html'
    success_url = reverse_lazy('core:post_type_list')
