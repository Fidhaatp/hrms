from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

from core.models import UserProfile

FORM_CONTROL = {"class": "form-control"}


class LoginForm(AuthenticationForm):
    """Sign in with username or email."""

    username = forms.CharField(
        label="Username or email",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Username or email", "autofocus": True}
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}),
    )

    def clean_username(self):
        value = self.cleaned_data.get("username", "").strip()
        if "@" in value:
            user = User.objects.filter(email__iexact=value).first()
            if user:
                return user.get_username()
        return value

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")
        if username and password:
            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )
            if self.user_cache is None:
                raise forms.ValidationError("Invalid username/email or password.")
            self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data


class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("profile_picture",)
        widgets = {
            "profile_picture": forms.FileInput(
                attrs={**FORM_CONTROL, "accept": "image/*"}
            ),
        }
