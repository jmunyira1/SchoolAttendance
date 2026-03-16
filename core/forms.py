# core/forms.py

from django import forms
from .models import AcademicYear, Term, NonSchoolDay, LateThreshold, SchoolDayConfig


class AcademicYearForm(forms.ModelForm):
    class Meta:
        model   = AcademicYear
        fields  = ['year', 'is_current']
        widgets = {
            'year'      : forms.NumberInput(attrs={'class': 'form-control'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TermForm(forms.ModelForm):
    class Meta:
        model   = Term
        fields  = ['academic_year', 'term_number', 'start_date', 'end_date', 'is_current']
        widgets = {
            'academic_year' : forms.Select(attrs={'class': 'form-select'}),
            'term_number'   : forms.Select(attrs={'class': 'form-select'}),
            'start_date'    : forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date'      : forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current'    : forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class NonSchoolDayForm(forms.ModelForm):
    class Meta:
        model   = NonSchoolDay
        fields  = ['date', 'name', 'day_type']
        widgets = {
            'date'      : forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'name'      : forms.TextInput(attrs={'class': 'form-control'}),
            'day_type'  : forms.Select(attrs={'class': 'form-select'}),
        }


class LateThresholdForm(forms.ModelForm):
    class Meta:
        model   = LateThreshold
        fields  = ['day_type', 'cutoff_time', 'applies_to']
        widgets = {
            'day_type'      : forms.Select(attrs={'class': 'form-select'}),
            'cutoff_time'   : forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'applies_to'    : forms.Select(attrs={'class': 'form-select'}),
        }


class SchoolDayConfigForm(forms.ModelForm):
    class Meta:
        model   = SchoolDayConfig
        fields  = ['stream', 'day_of_week']
        widgets = {
            'stream'        : forms.Select(attrs={'class': 'form-select'}),
            'day_of_week'   : forms.Select(attrs={'class': 'form-select'}),
        }