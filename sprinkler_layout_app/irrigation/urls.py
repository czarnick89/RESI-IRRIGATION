from django.urls import path, include
from .views import HelloView, LogoutView, RegisterView, PasswordResetRequestView, PasswordResetConfirmView, VerifyEmailView, CustomTokenObtainPairView, ProjectViewSet, YardViewSet, SprinklerHeadViewSet, ZoneViewSet, BillOfMaterialsViewSet, SketchElementViewSet
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'yards', YardViewSet, basename='yard')
router.register(r'sprinkler-heads', SprinklerHeadViewSet, basename='sprinklerhead')
router.register(r'zones', ZoneViewSet, basename='zone')
router.register(r'bom', BillOfMaterialsViewSet, basename='bom')
router.register(r'sketch-elements', SketchElementViewSet, basename='sketchelement')


urlpatterns = [
    path('hello/', HelloView.as_view(), name='hello'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]