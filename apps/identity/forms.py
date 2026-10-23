from django import forms
from django.contrib.auth.forms import AuthenticationForm


class SignInForm(AuthenticationForm):
    username = forms.EmailField(
        label="E-Mail-Adresse",
        widget=forms.EmailInput(attrs={"autocomplete": "username", "autofocus": True}),
    )
    password = forms.CharField(
        label="Passwort",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    error_messages = {
        "invalid_login": "E-Mail-Adresse oder Passwort ist nicht korrekt.",
        "inactive": "E-Mail-Adresse oder Passwort ist nicht korrekt.",
    }
