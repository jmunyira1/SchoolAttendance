# people/forms.py

from django import forms
from .models import Form, Stream, Student, StaffMember


class FormForm(forms.ModelForm):
    class Meta:
        model   = Form
        fields  = ['name', 'order']
        widgets = {
            'name'  : forms.TextInput(attrs={'class': 'form-control'}),
            'order' : forms.NumberInput(attrs={'class': 'form-control'}),
        }


class StreamForm(forms.ModelForm):
    class Meta:
        model   = Stream
        fields  = ['form', 'name']
        widgets = {
            'form'  : forms.Select(attrs={'class': 'form-select'}),
            'name'  : forms.TextInput(attrs={'class': 'form-control'}),
        }


class StudentForm(forms.ModelForm):
    class Meta:
        model   = Student
        fields  = ['admission_number', 'full_name', 'stream', 'date_of_birth', 'gender', 'photo', 'zk_user_id', 'is_active']
        widgets = {
            'admission_number'  : forms.TextInput(attrs={'class': 'form-control'}),
            'full_name'         : forms.TextInput(attrs={'class': 'form-control'}),
            'stream'            : forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth'     : forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender'            : forms.Select(attrs={'class': 'form-select'}),
            'zk_user_id'        : forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active'         : forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class StaffMemberForm(forms.ModelForm):
    class Meta:
        model   = StaffMember
        fields  = ['staff_id', 'full_name', 'staff_type', 'designation', 'photo', 'zk_user_id', 'is_active']
        widgets = {
            'staff_id'      : forms.TextInput(attrs={'class': 'form-control'}),
            'full_name'     : forms.TextInput(attrs={'class': 'form-control'}),
            'staff_type'    : forms.Select(attrs={'class': 'form-select'}),
            'designation'   : forms.TextInput(attrs={'class': 'form-control'}),
            'zk_user_id'    : forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active'     : forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }