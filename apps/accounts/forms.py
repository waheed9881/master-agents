"""Forms for authentication, team management, and onboarding."""
from django import forms

from apps.accounts.models import UserRole


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)



class TeamInviteForm(forms.Form):
    email = forms.EmailField()
    full_name = forms.CharField(max_length=255)
    role = forms.ChoiceField(choices=UserRole.choices)
    send_invite_placeholder = forms.BooleanField(
        required=False,
        initial=False,
        label="Show invite placeholder (no email sent)",
    )


class TeamMemberEditForm(forms.Form):
    full_name = forms.CharField(max_length=255)
    role = forms.ChoiceField(choices=UserRole.choices)
    is_active = forms.BooleanField(required=False, initial=True)


class OnboardingWorkspaceForm(forms.Form):
    name = forms.CharField(max_length=255)
    country = forms.CharField(max_length=64, required=False)
    industry = forms.CharField(max_length=128, required=False)
    timezone = forms.CharField(max_length=64, initial="UTC")
    default_currency = forms.CharField(max_length=8, initial="USD")
    business_description = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )
