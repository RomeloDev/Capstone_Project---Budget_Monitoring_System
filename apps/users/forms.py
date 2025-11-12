"""
Forms for user authentication and password reset
"""
from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset via email"""

    email = forms.EmailField(
        max_length=255,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email',
            'required': True,
        })
    )

    def clean_email(self):
        """Normalize email (lowercase and strip whitespace)"""
        email = self.cleaned_data.get('email')
        if email:
            return email.lower().strip()
        return email


class SetPasswordForm(forms.Form):
    """Form for setting new password after reset"""

    new_password1 = forms.CharField(
        label="New Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition',
            'placeholder': 'Enter new password',
            'autocomplete': 'new-password',
            'required': True,
        }),
        help_text="Password must be at least 8 characters and include letters and numbers"
    )

    new_password2 = forms.CharField(
        label="Confirm New Password",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none transition',
            'placeholder': 'Confirm new password',
            'autocomplete': 'new-password',
            'required': True,
        })
    )

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password1(self):
        """Validate password using Django's built-in validators"""
        password = self.cleaned_data.get('new_password1')
        if password and self.user:
            try:
                validate_password(password, self.user)
            except ValidationError as e:
                raise ValidationError(e.messages)
        return password

    def clean_new_password2(self):
        """Check that both passwords match"""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields didn't match.")

        return password2

    def save(self, commit=True):
        """Save the new password for the user"""
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user
