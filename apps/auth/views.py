from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.auth.serializers import (
    LoginSerializer,
    LogoutSerializer,
    MeSerializer,
    RefreshSerializer,
)
from apps.users.models import User


def _issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "acces": str(refresh.access_token),
        "refresh": str(refresh),
    }


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get_authenticate_header(self, request):
        return 'Bearer realm="api"'

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["login"].lower()
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed("Неверный логин или пароль")

        if not user.is_active or not user.check_password(password):
            raise AuthenticationFailed("Неверный логин или пароль")

        return Response(_issue_tokens(user))


class RefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get_authenticate_header(self, request):
        return 'Bearer realm="api"'

    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            old = RefreshToken(serializer.validated_data["token"])
        except TokenError:
            raise AuthenticationFailed("Невалидный refresh token")

        user_id = old.payload.get("user_id")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed("Пользователь не найден")

        try:
            old.blacklist()
        except AttributeError:
            pass

        return Response(_issue_tokens(user))


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError:
            raise AuthenticationFailed("Невалидный refresh token")
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)
