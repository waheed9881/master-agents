from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.accounts.forms import LoginForm
from apps.accounts.rate_limit import get_rate_limit_for_scope, rate_limit_or_429
from apps.accounts.services import authenticate_user
from apps.tenants.audit import log_audit_event


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    form = LoginForm(request.POST or None)
    error = None

    if request.method == "POST" and form.is_valid():
        limit, window = get_rate_limit_for_scope("login")
        blocked = rate_limit_or_429(
            request, "login", limit, window, json_response=False
        )
        if blocked:
            error = blocked.content.decode() if hasattr(blocked, "content") else "Too many login attempts."
        else:
            user = authenticate_user(
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
            if user:
                login(request, user)
                log_audit_event(
                    action="login_success",
                    tenant=user.tenant,
                    user=user,
                    object_type="user",
                    object_id=user.pk,
                    request=request,
                )
                next_url = request.GET.get("next")
                if next_url:
                    return redirect(next_url)
                return redirect("dashboard:index")
            log_audit_event(
                action="login_failure",
                object_type="user",
                metadata={"email": form.cleaned_data["email"]},
                request=request,
            )
            error = "Invalid email or password."

    return render(
        request,
        "auth/login.html",
        {"form": form, "error": error},
    )


@login_required
@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    return redirect("accounts:login")
