from django import forms
from jalali_date.widgets import AdminJalaliDateWidget
from .models import Soldier, Leave


class SoldierForm(forms.ModelForm):
    class Meta:
        model = Soldier
        fields = '__all__'
        widgets = {
            # Update usage here as well
            'service_start_date': AdminJalaliDateWidget(),
            'arrival_date': AdminJalaliDateWidget(),
            'birth_date': AdminJalaliDateWidget(),
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class LeaveForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = '__all__'
        widgets = {
            # Update usage here as well
            'start_date': AdminJalaliDateWidget(),
            'end_date': AdminJalaliDateWidget(),
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class SettingsForm(forms.Form):
    base_service_months = forms.IntegerField(label="مدت پایه خدمت (ماه)", min_value=1, initial=21)
    enable_leave_entitlement = forms.BooleanField(label="فعال بودن مرخصی استحقاقی", required=False, initial=True)
    enable_leave_medical = forms.BooleanField(label="فعال بودن مرخصی استعلاجی", required=False, initial=True)
    enable_leave_reward = forms.BooleanField(label="فعال بودن مرخصی تشویقی", required=False, initial=True)


class ExcelImportForm(forms.Form):
    file = forms.FileField()


class ExcelImportConfirmForm(forms.Form):
    token = forms.CharField(widget=forms.HiddenInput)  # برای نگه داشتن نتیجه parse در session/cache
