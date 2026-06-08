from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5 "
                "focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none",
                "placeholder": "you@company.com",
                "autocomplete": "email",
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full rounded-lg border border-gray-300 px-4 py-2.5 "
                "focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none",
                "placeholder": "••••••••",
                "autocomplete": "current-password",
            }
        )
    )
