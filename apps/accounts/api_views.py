from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.rate_limit import get_rate_limit_for_scope, rate_limit_or_429
from apps.accounts.serializers import LoginSerializer, UserSerializer
from apps.accounts.services import authenticate_user
from apps.tenants.audit import log_audit_event


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        limit, window = get_rate_limit_for_scope("login")
        blocked = rate_limit_or_429(request, "login", limit, window)
        if blocked:
            return blocked

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if not user:
            log_audit_event(
                action="login_failure",
                object_type="user",
                metadata={"email": serializer.validated_data["email"]},
                request=request,
            )
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        from django.contrib.auth import login

        login(request, user)
        log_audit_event(
            action="login_success",
            tenant=user.tenant,
            user=user,
            object_type="user",
            object_id=user.pk,
            request=request,
        )
        return Response(UserSerializer(user).data)


class LogoutAPIView(APIView):
    def post(self, request):
        from django.contrib.auth import logout

        logout(request)
        return Response({"detail": "Logged out."})


class MeAPIView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)
