from django import forms
from jalali_date.widgets import AdminJalaliDateWidget

from .models import Soldier, Leave


class SoldierForm(forms.ModelForm):
    class Meta:
        model = Soldier
        fields = '__all__'
        widgets = {
            'service_start_date': AdminJalaliDateWidget(),
            'arrival_date': AdminJalaliDateWidget(),
            'birth_date': AdminJalaliDateWidget(),
        }

    def clean(self):
        cleaned_data = super().clean()

        has_dl = cleaned_data.get('has_driving_license')
        dl_type = cleaned_data.get('driving_license_type')
        if has_dl is False and dl_type:
            self.add_error('driving_license_type', 'وقتی گواهینامه ندارد، نوع گواهینامه نباید انتخاب شود.')

        mr_ref = cleaned_data.get('military_rank_ref')
        mr_code = cleaned_data.get('military_rank')
        if mr_ref and (mr_code is None or mr_code == ''):
            cleaned_data['military_rank'] = mr_ref.code

        return cleaned_data


class LeaveForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = '__all__'
        widgets = {
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
    token = forms.CharField(widget=forms.HiddenInput)
