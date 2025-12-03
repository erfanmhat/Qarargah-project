from django import forms
from .models import Soldier, Leave


class JalaliDateInput(forms.DateInput):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs'].update({
            'class': 'form-control jalali-date',
            'placeholder': '1404/09/12',
            'autocomplete': 'off'
        })
        super().__init__(*args, **kwargs, format='%Y-%m-%d')


class SoldierForm(forms.ModelForm):
    class Meta:
        model = Soldier
        fields = '__all__'
        widgets = {
            'service_start_date': JalaliDateInput(),
            'arrival_date': JalaliDateInput(),
            'birth_date': JalaliDateInput(),
        }


class LeaveForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = '__all__'
        widgets = {
            'start_date': JalaliDateInput(),
            'end_date': JalaliDateInput(),
        }
