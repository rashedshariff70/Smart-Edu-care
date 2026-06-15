from django import forms
from .models import StudentRegistration, StudentLogin


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = StudentRegistration
        fields = ['college_name', 'college_email', 'college_id', 'password']

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('password_confirm'):
            raise forms.ValidationError("Passwords do not match!")
        return cleaned_data


class LoginForm(forms.Form):
    college_id = forms.CharField(max_length=50, label="College ID")
    college_name = forms.CharField(max_length=150, label="College Name")
    password = forms.CharField(widget=forms.PasswordInput)