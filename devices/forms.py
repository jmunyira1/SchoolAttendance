# devices/forms.py

from django import forms
from .models import Device


class DeviceForm(forms.ModelForm):
    class Meta:
        model   = Device
        fields  = ['name', 'ip_address', 'port', 'location', 'is_active']
        widgets = {
            'name'          : forms.TextInput(attrs={'class': 'form-control'}),
            'ip_address'    : forms.TextInput(attrs={'class': 'form-control'}),
            'port'          : forms.NumberInput(attrs={'class': 'form-control'}),
            'location'      : forms.TextInput(attrs={'class': 'form-control'}),
            'is_active'     : forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }