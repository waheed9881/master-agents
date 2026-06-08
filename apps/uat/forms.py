"""UAT and feedback forms."""
from django import forms

from apps.uat.models import (
    ChecklistItemStatus,
    FeedbackCategory,
    FeedbackItem,
    FeedbackPriority,
    FeedbackStatus,
    UATChecklistItem,
    UATSession,
)


class UATSessionForm(forms.ModelForm):
    class Meta:
        model = UATSession
        fields = ["title", "demo_version", "audience", "facilitator", "summary"]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
        }


class UATChecklistItemForm(forms.ModelForm):
    class Meta:
        model = UATChecklistItem
        fields = ["section", "title", "description", "expected_result", "order"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 2}),
            "expected_result": forms.Textarea(attrs={"rows": 2}),
        }


class ChecklistStatusForm(forms.Form):
    item_id = forms.IntegerField(widget=forms.HiddenInput)
    status = forms.ChoiceField(choices=ChecklistItemStatus.choices)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))


class FeedbackItemForm(forms.ModelForm):
    class Meta:
        model = FeedbackItem
        fields = [
            "title",
            "description",
            "category",
            "priority",
            "status",
            "module_area",
            "session",
            "related_url",
            "screenshot_note",
            "assigned_to",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "session": forms.Select(attrs={"class": "w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"}),
        }

    def __init__(self, *args, tenant=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant:
            self.fields["session"].queryset = UATSession.objects.filter(tenant=tenant)
            self.fields["session"].required = False
            from apps.accounts.models import User

            self.fields["assigned_to"].queryset = User.objects.filter(tenant=tenant, is_active=True)
            self.fields["assigned_to"].required = False
        from apps.uat.permissions import can_participate_uat

        if user and not can_participate_uat(user):
            self.fields["status"].widget = forms.HiddenInput()
            self.fields["assigned_to"].widget = forms.HiddenInput()
            self.fields["status"].required = False
            self.fields["assigned_to"].required = False
            self.fields["status"].initial = FeedbackStatus.OPEN

    def clean_status(self):
        status = self.cleaned_data.get("status")
        if not status:
            return FeedbackStatus.OPEN
        return status
