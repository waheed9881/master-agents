from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import LoginSerializer, UserSerializer
from apps.accounts.services import authenticate_user


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate_user(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if not user:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        from django.contrib.auth import login

        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutAPIView(APIView):
    def post(self, request):
        from django.contrib.auth import logout

        logout(request)
        return Response({"detail": "Logged out."})


class MeAPIView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)
