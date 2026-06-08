from django import forms

from apps.inbox.models import ChannelAccount, ChannelType


class ChannelAccountForm(forms.Form):
    channel_type = forms.ChoiceField(choices=ChannelType.choices)
    display_name = forms.CharField(max_length=255)
    phone_number_id = forms.CharField(max_length=128, required=False)
    business_account_id = forms.CharField(max_length=128, required=False)
    instagram_page_id = forms.CharField(max_length=128, required=False, label="Instagram page ID")
    verify_token = forms.CharField(max_length=255, required=False)
    access_token = forms.CharField(
        max_length=512,
        required=False,
        widget=forms.PasswordInput(render_value=True),
        help_text="Optional in mock mode",
    )
    app_secret = forms.CharField(
        max_length=512,
        required=False,
        widget=forms.PasswordInput(render_value=True),
        help_text="Optional in mock mode",
    )
    is_active = forms.BooleanField(required=False, initial=True)
    mock_mode = forms.BooleanField(
        required=False,
        initial=True,
        help_text="Use local mock mode (no real Meta API calls)",
    )

    def clean(self):
        cleaned = super().clean()
        channel_type = cleaned.get("channel_type")
        mock_mode = cleaned.get("mock_mode", True)

        if channel_type == ChannelType.WHATSAPP and not cleaned.get("phone_number_id"):
            if not mock_mode:
                self.add_error("phone_number_id", "Required for WhatsApp in live mode.")
            elif not cleaned.get("phone_number_id"):
                cleaned["phone_number_id"] = f"mock_wa_{cleaned.get('display_name', 'channel')[:20]}"

        if channel_type == ChannelType.INSTAGRAM and not cleaned.get("instagram_page_id"):
            if not mock_mode:
                self.add_error("instagram_page_id", "Required for Instagram in live mode.")
            elif not cleaned.get("instagram_page_id"):
                cleaned["instagram_page_id"] = f"mock_ig_{cleaned.get('display_name', 'channel')[:20]}"

        if not mock_mode:
            missing = []
            if not cleaned.get("access_token"):
                missing.append("access token")
            if channel_type in (ChannelType.WHATSAPP, ChannelType.INSTAGRAM) and not cleaned.get("app_secret"):
                missing.append("app secret")
            if missing:
                raise forms.ValidationError(
                    f"Live mode requires: {', '.join(missing)}. Enable mock mode for local demo."
                )

        return cleaned


class ChannelTestForm(forms.Form):
    message_text = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    customer_name = forms.CharField(max_length=255, initial="Test Customer")
    customer_phone = forms.CharField(max_length=64, required=False)
    customer_username = forms.CharField(max_length=128, required=False)
    agent_instance_id = forms.IntegerField()
