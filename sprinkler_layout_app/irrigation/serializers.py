from django.contrib.auth.models import User
from rest_framework import serializers
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Project, Yard, SprinklerHead, Zone, BillOfMaterials, SketchElement

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        user.is_active = False  # User must verify email before login
        user.save()
        return user

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    uidb64 = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_active:
            raise serializers.ValidationError("Email not verified. Please check your email.")
        return data
    
class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

class SketchElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = SketchElement
        fields = '__all__'

class SprinklerHeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SprinklerHead
        fields = '__all__'
        read_only_fields = ['head_number'] 

class ZoneSerializer(serializers.ModelSerializer):
    sprinkler_heads = SprinklerHeadSerializer(many=True, read_only=True)

    class Meta:
        model = Zone
        fields = '__all__'
        read_only_fields = ['zone_number'] 

class YardSerializer(serializers.ModelSerializer):
    zones = ZoneSerializer(many=True, read_only=True)
    sketch_elements = SketchElementSerializer(many=True, read_only=True)

    class Meta:
        model = Yard
        fields = '__all__'

class BillOfMaterialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillOfMaterials
        fields = '__all__'