# accounts/forms.py

from django import forms
from .models import User


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )


class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Leave blank to keep existing password when editing.'
    )

    class Meta:
        model   = User
        fields  = ['username', 'full_name', 'role', 'is_active']
        widgets = {
            'username'  : forms.TextInput(attrs={'class': 'form-control'}),
            'full_name' : forms.TextInput(attrs={'class': 'form-control'}),
            'role'      : forms.Select(attrs={'class': 'form-select'}),
            'is_active' : forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # password required only when creating a new user
        if not self.instance.pk and not cleaned_data.get('password'):
            self.add_error('password', 'Password is required for new users.')
        return cleaned_data