from django import forms
from django.core.exceptions import ValidationError
from django import forms
from core.models import Leave, Soldier
import jdatetime

class SoldierForm(forms.ModelForm):
    """فرم ایجاد و ویرایش سرباز"""
    
    class Meta:
        model = Soldier
        fields = ['first_name', 'last_name', 'national_code']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام',
                'dir': 'rtl'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام خانوادگی',
                'dir': 'rtl'
            }),
            'national_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'کد ملی (۱۰ رقم)',
                'maxlength': '10',
                'dir': 'ltr'
            }),
        }

    def clean_national_code(self):
        """اعتبارسنجی کد ملی"""
        national_code = self.cleaned_data.get('national_code')
        if not national_code:
            raise ValidationError("کد ملی الزامی است.")
        if not national_code.isdigit():
            raise ValidationError("کد ملی باید فقط شامل اعداد باشد.")
        if len(national_code) != 10:
            raise ValidationError("کد ملی باید ۱۰ رقم باشد.")
        
        qs = Soldier.objects.filter(national_code=national_code)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("سربازی با این کد ملی قبلاً ثبت شده است.")
        
        return national_code
    
    def _convert_fa_to_en_numbers(self, date_str):
        """تبدیل کاراکترهای اعداد فارسی و عربی به اعداد انگلیسی استاندارد"""
        persian_numbers = '۰۱۲۳۴۵۶۷۸۹'
        arabic_numbers = '٠١٢٣٤٥٦٧٨٩'
        english_numbers = '0123456789'
        
        # ساخت یک جدول نگاشت برای ترجمه کاراکترها
        translation_table = str.maketrans(
            persian_numbers + arabic_numbers, 
            english_numbers + english_numbers
        )
        return date_str.translate(translation_table)

    def clean(self):
        # با اصلاح متدهای بالایی، super().clean() دیگر دچار خطای کاذب روی فیلدها نخواهد شد
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        
        if first_name and last_name:
            if first_name.strip() == '' or last_name.strip() == '':
                raise ValidationError("نام و نام خانوادگی نمی‌توانند خالی باشند.")
        
        return cleaned_data


class SoldierSearchForm(forms.Form):
    """فرم جستجوی سربازان"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'جستجو بر اساس نام، نام خانوادگی یا کد ملی',
            'dir': 'rtl'
        })
    )


class LeaveForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = [
            "soldier",
            "leave_type",
            "start_date",
            "days",
            "description",
        ]
        widgets = {
            "soldier": forms.Select(attrs={"class": "form-control"}),

            "leave_type": forms.Select(attrs={"class": "form-control"}),

            "start_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),

            "days": forms.NumberInput(
                attrs={"class": "form-control", "min": 1}
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "توضیحات مرخصی"
                }
            ),
        }

        labels = {
            "soldier": "سرباز",
            "leave_type": "نوع مرخصی",
            "start_date": "تاریخ شروع",
            "days": "تعداد روز",
            "description": "توضیحات",
        }


class LeaveSearchForm(forms.Form):

    soldier = forms.ModelChoiceField(
        queryset=Soldier.objects.all(),
        required=False,
        label="سرباز",
        widget=forms.Select(attrs={"class": "form-control"})
    )

    leave_type = forms.ChoiceField(
        choices=[("", "همه")] + list(Leave.LEAVE_TYPES),
        required=False,
        label="نوع مرخصی",
        widget=forms.Select(attrs={"class": "form-control"})
    )

    start_date = forms.DateField(
        required=False,
        label="از تاریخ",
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        )
    )

    active_only = forms.BooleanField(
        required=False,
        label="فقط مرخصی‌های فعال",
        widget=forms.CheckboxInput()
    )
