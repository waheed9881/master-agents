"""Forms for workspace and plan settings."""
from django import forms

from apps.tenants.models import Plan, Tenant


class WorkspaceSettingsForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = [
            "name",
            "slug",
            "country",
            "industry",
            "timezone",
            "default_currency",
            "business_description",
            "support_email",
            "support_phone",
        ]
        widgets = {
            "business_description": forms.Textarea(attrs={"rows": 4}),
            "timezone": forms.TextInput(attrs={"placeholder": "UTC or America/New_York"}),
        }


class PlanChangeForm(forms.Form):
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True),
        empty_label=None,
    )


class DemoResetForm(forms.Form):
    confirm = forms.CharField(
        label="Type RESET to confirm",
        max_length=10,
    )
    action = forms.CharField(widget=forms.HiddenInput())

    def clean_confirm(self):
        value = self.cleaned_data["confirm"].strip().upper()
        if value != "RESET":
            raise forms.ValidationError("Please type RESET to confirm.")
        return value
