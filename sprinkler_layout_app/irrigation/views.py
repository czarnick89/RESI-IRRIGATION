from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from .serializers import RegisterSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer, CustomTokenObtainPairSerializer
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.contrib.auth.models import User
from .utils import generate_verification_token, verify_email_token
from rest_framework_simplejwt.views import TokenObtainPairView

class HelloView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(data={"message": f"Hello, {request.user.username}!"})
    
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"detail": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"error": "Invalid token or already blacklisted"}, status=status.HTTP_400_BAD_REQUEST)

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = generate_verification_token(user)
            verification_link = f"http://localhost:3000/verify-email/?token={token}"

            send_mail(
                subject="Verify Your Email",
                message=f"Please verify your email by clicking the link: {verification_link}",
                from_email="noreply@resirrigation.com",
                recipient_list=[user.email],
            )

            return Response({"message": "Registration successful. Check your email to verify your account."}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get('token')
        user_pk = verify_email_token(token)

        if user_pk is None:
            return Response({"error": "Invalid or expired verification link"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=user_pk)
            if user.is_active:
                return Response({"message": "Account already verified"}, status=status.HTTP_200_OK)

            user.is_active = True
            user.save()
            return Response({"message": "Email verified successfully. You may now log in."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                token_generator = PasswordResetTokenGenerator()
                token = token_generator.make_token(user)
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

                reset_link = f"http://yourfrontend.com/reset-password/{uidb64}/{token}/"

                # Send email (in this example, just print to console)
                send_mail(
                    subject="Password Reset Request",
                    message=f"Use this link to reset your password: {reset_link}",
                    from_email=None,
                    recipient_list=[email],
                )
                return Response({"detail": "Password reset link sent"}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                # For security, don't reveal user existence
                return Response({"detail": "Password reset link sent"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            try:
                uidb64 = serializer.validated_data['uidb64']
                token = serializer.validated_data['token']
                new_password = serializer.validated_data['new_password']

                uid = force_str(urlsafe_base64_decode(uidb64))
                user = User.objects.get(pk=uid)

                token_generator = PasswordResetTokenGenerator()
                if not token_generator.check_token(user, token):
                    return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

                user.set_password(new_password)
                user.save()
                return Response({"detail": "Password has been reset successfully"}, status=status.HTTP_200_OK)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                return Response({"error": "Invalid token or user"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer