from django import forms
from django.core.exceptions import ValidationError

from .models import (
    DailySchedule,
    Leave,
    LeaveType,
    PostAssignment,
    PostType,
    ShiftConfig,
    Soldier,
    SoldierRole,
    HealthType,
)


# ─────────────────────────────────────────
#  سرباز
# ─────────────────────────────────────────

class SoldierForm(forms.ModelForm):
    class Meta:
        model = Soldier
        fields = [
            "full_name",
            "national_code",
            "health_type",
            "role",
            "has_driving_license",
            "driving_license_type",
            "is_active",
            "notes",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "نام و نام خانوادگی",
                "autofocus": True,
            }),
            "national_code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "کد ملی ۱۰ رقمی",
                "maxlength": "10",
                "inputmode": "numeric",
            }),
            "health_type": forms.Select(attrs={"class": "form-select"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "has_driving_license": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "driving_license_type": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "توضیحات اختیاری ...",
            }),
        }
        labels = {
            "full_name": "نام و نام خانوادگی",
            "national_code": "کد ملی",
            "health_type": "وضعیت سلامت",
            "role": "نقش / تخصص",
            "has_driving_license": "دارای گواهینامه رانندگی",
            "driving_license_type": "نوع گواهینامه",
            "is_active": "در خدمت است؟",
            "notes": "توضیحات",
        }

    def clean(self):
        cleaned = super().clean()
        has_license = cleaned.get("has_driving_license")
        license_type = cleaned.get("driving_license_type")
        if not has_license and license_type:
            raise ValidationError(
                {"driving_license_type": "وقتی گواهینامه ندارد، نوع گواهینامه نباید انتخاب شود."}
            )
        return cleaned


# ─────────────────────────────────────────
#  مرخصی
# ─────────────────────────────────────────

class LeaveForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = ["leave_type", "start_date", "days", "notes"]
        widgets = {
            "leave_type": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "days": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
                "max": "30",
                "placeholder": "تعداد روز",
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "توضیحات اختیاری ...",
            }),
        }
        labels = {
            "leave_type": "نوع مرخصی",
            "start_date": "تاریخ شروع",
            "days": "تعداد روز",
            "notes": "توضیحات",
        }


# ─────────────────────────────────────────
#  تنظیمات — پاس
# ─────────────────────────────────────────

class ShiftConfigForm(forms.ModelForm):
    class Meta:
        model = ShiftConfig
        fields = ["name", "start_time", "end_time", "order", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "مثال: پاس اول"}),
            "start_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "end_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "name": "نام پاس",
            "start_time": "ساعت شروع",
            "end_time": "ساعت پایان",
            "order": "ترتیب",
            "is_active": "فعال",
        }


# ─────────────────────────────────────────
#  تنظیمات — نوع پست
# ─────────────────────────────────────────

class PostTypeForm(forms.ModelForm):
    # چک‌باکس‌های پویا برای وضعیت سلامت مجاز
    allowed_health_types = forms.MultipleChoiceField(
        choices=HealthType.choices,
        widget=forms.CheckboxSelectMultiple,
        label="وضعیت سلامت مجاز",
        required=True,
    )

    class Meta:
        model = PostType
        fields = [
            "name",
            "allowed_health_types",
            "soldiers_per_shift",
            "shift_count",
            "is_shift_based",
            "is_active",
            "order",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "نام پست"}),
            "soldiers_per_shift": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "shift_count": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "is_shift_based": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
        }
        labels = {
            "name": "نام پست",
            "soldiers_per_shift": "تعداد سرباز در هر پاس",
            "shift_count": "تعداد پاس",
            "is_shift_based": "پاس‌بندی دارد؟",
            "is_active": "فعال",
            "order": "ترتیب نمایش",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # مقدار اولیه از JSONField
        if self.instance.pk and self.instance.allowed_health_types:
            self.initial["allowed_health_types"] = self.instance.allowed_health_types

    def clean_allowed_health_types(self):
        # تبدیل list به JSON-compatible list
        return list(self.cleaned_data["allowed_health_types"])


# ─────────────────────────────────────────
#  تنظیمات — نقش سرباز
# ─────────────────────────────────────────

class SoldierRoleForm(forms.ModelForm):
    class Meta:
        model = SoldierRole
        fields = ["title", "order"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "مثال: راننده"}),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
        }
        labels = {
            "title": "عنوان نقش",
            "order": "ترتیب نمایش",
        }


# ─────────────────────────────────────────
#  برنامه روزانه — override دستی یک پست
# ─────────────────────────────────────────

class AssignSoldierForm(forms.Form):
    """فرم ساده برای انتخاب دستی سرباز برای یک پست/پاس"""
    soldier_id = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, soldiers_qs=None, **kwargs):
        super().__init__(*args, **kwargs)
        # soldiers_qs اختیاری است — برای validation استفاده می‌شود
        self._soldiers_qs = soldiers_qs

    def clean_soldier_id(self):
        sid = self.cleaned_data["soldier_id"]
        if self._soldiers_qs is not None:
            if not self._soldiers_qs.filter(pk=sid).exists():
                raise ValidationError("سرباز انتخاب‌شده معتبر نیست.")
        return sid


# ─────────────────────────────────────────
#  فیلتر لیست سربازان
# ─────────────────────────────────────────

class SoldierFilterForm(forms.Form):
    HEALTH_CHOICES = [("", "همه")] + HealthType.choices
    STATUS_CHOICES = [
        ("", "همه"),
        ("active", "در خدمت"),
        ("on_leave", "در مرخصی"),
    ]

    health_type = forms.ChoiceField(
        choices=HEALTH_CHOICES,
        required=False,
        label="وضعیت سلامت",
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label="وضعیت",
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    search = forms.CharField(
        required=False,
        label="جستجو",
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-sm",
            "placeholder": "نام یا کد ملی ...",
        }),
    )