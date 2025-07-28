# Django imports
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

# DRF imports
from rest_framework import status, permissions, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action, api_view, permission_classes

# JWT imports
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken, OutstandingToken
)

# App imports
from .models import (
    Project, Yard, SprinklerHead, Zone, BillOfMaterials, SketchElement
)
from .serializers import (
    RegisterSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    CustomTokenObtainPairSerializer,
    ProjectSerializer,
    YardSerializer,
    SprinklerHeadSerializer,
    ZoneSerializer,
    BillOfMaterialsSerializer,
    SketchElementSerializer,
    FullProjectSetupSerializer,
)
from .utils import generate_verification_token, verify_email_token, sanitize_layout_data
from .layout_utils import parse_yard_geometry
from shapely.geometry import Polygon
from irrigation.layout.generator import generate_sprinkler_layout

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

class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'project') and hasattr(obj.project, 'user'):
            return obj.project.user == request.user
        if hasattr(obj, 'yard') and hasattr(obj.yard, 'project') and hasattr(obj.yard.project, 'user'):
            return obj.yard.project.user == request.user
        if hasattr(obj, 'zone') and hasattr(obj.zone, 'yard') and hasattr(obj.zone.yard, 'project') and hasattr(obj.zone.yard.project, 'user'):
            return obj.zone.yard.project.user == request.user
        return False
    
class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='full-setup')
    def create_full_project(self, request):
        serializer = FullProjectSetupSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            project = serializer.save()
            return Response({
                "message": "Full project setup created successfully",
                "project_id": project.id
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='generate-layout')
    def generate_layout(self, request):
        yard_id = request.data.get("yard_id")

        if not yard_id:
            return Response({"error": "yard_id is required"}, status=400)

        try:
            yard = Yard.objects.get(id=yard_id, project__user=request.user)
        except Yard.DoesNotExist:
            return Response({"error": "Yard not found"}, status=404)

        usable_area = parse_yard_geometry(yard)

        #print("USABLE AREA:", usable_area)  # for dev inspection

        if usable_area.is_empty:
            area_bounds = None
            sprinklers = []
        else:
            area_bounds = usable_area.bounds
            sprinklers = generate_sprinkler_layout(yard)

        raw_response = {
        "status": "sprinklers_generated",
        "area_bounds": area_bounds,
        "sprinklers": sprinklers,
        "zones": []  # <- stub for future zoning logic
        }

        return Response(sanitize_layout_data(raw_response), status=200)
     
class YardViewSet(viewsets.ModelViewSet):
    serializer_class = YardSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Yard.objects.filter(project__user=self.request.user)
    def perform_create(self, serializer):
        project_id = self.request.data.get('project')
        try:
            project = Project.objects.get(id=project_id, user=self.request.user)
        except Project.DoesNotExist:
            raise PermissionDenied("Invalid project or you do not have permission to add to it.")
        
        serializer.save(project=project)
    
class ZoneViewSet(viewsets.ModelViewSet):
    serializer_class = ZoneSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Zone.objects.filter(yard__project__user=self.request.user)
    
    def perform_create(self, serializer):
        yard_id = self.request.data.get('yard')
        try:
            yard = Yard.objects.get(id=yard_id, project__user=self.request.user)
        except Yard.DoesNotExist:
            raise PermissionDenied("Invalid yard or you do not have permission to add to it.")
        
        serializer.save(yard=yard)
    
class SprinklerHeadViewSet(viewsets.ModelViewSet):
    serializer_class = SprinklerHeadSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return SprinklerHead.objects.filter(zone__yard__project__user=self.request.user)
    
    def perform_create(self, serializer):
        zone_id = self.request.data.get('zone')
        try:
            zone = Zone.objects.get(id=zone_id, yard__project__user=self.request.user)
        except Zone.DoesNotExist:
            raise PermissionDenied("Invalid zone or you do not have permission to add to it.")
        
        serializer.save(zone=zone)
    
class BillOfMaterialsViewSet(viewsets.ModelViewSet):
    serializer_class = BillOfMaterialsSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return BillOfMaterials.objects.filter(project__user=self.request.user)
    
    def perform_create(self, serializer):
        project_id = self.request.data.get('project')
        try:
            project = Project.objects.get(id=project_id, user=self.request.user)
        except Project.DoesNotExist:
            raise PermissionDenied("Invalid project or you do not have permission to add to it.")
        
        serializer.save(project=project)
   
class SketchElementViewSet(viewsets.ModelViewSet):
    serializer_class = SketchElementSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return SketchElement.objects.filter(yard__project__user=self.request.user)
    
    def perform_create(self, serializer):
        yard_id = self.request.data.get('yard')
        try:
            yard = Yard.objects.get(id=yard_id, project__user=self.request.user)
        except Yard.DoesNotExist:
            raise PermissionDenied("Invalid yard or you do not have permission to add to it.")
        
        serializer.save(yard=yard)
