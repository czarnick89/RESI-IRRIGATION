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
        read_only_fields = ['created_at', 'updated_at', 'user']

    def create(self, validated_data):
        user = self.context['request'].user
        return Project.objects.create(user=user, **validated_data)

class SketchElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = SketchElement
        fields = '__all__'
        read_only_fields = ['yard']

    def create(self, validated_data):
        yard = self.context['yard']
        return SketchElement.objects.create(yard=yard, **validated_data)

class SprinklerHeadSerializer(serializers.ModelSerializer):
    location = serializers.JSONField(required=False)
    
    class Meta:
        model = SprinklerHead
        fields = '__all__'
        read_only_fields = ['head_number', 'zone']

    def create(self, validated_data):
        zone = self.context['zone']
        return SprinklerHead.objects.create(zone=zone, **validated_data)

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
        read_only_fields = ['project']

    def create(self, validated_data):
        project = self.context['project']
        return Yard.objects.create(project=project, **validated_data)

class BillOfMaterialsSerializer(serializers.ModelSerializer):   
    class Meta:
        model = BillOfMaterials
        fields = '__all__'

class FullProjectSetupSerializer(serializers.Serializer):
    project = ProjectSerializer()
    yard = YardSerializer()
    sprinkler_heads = SprinklerHeadSerializer(many=True)
    sketch_elements = SketchElementSerializer(many=True)

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None

        project_data = validated_data.pop('project')
        yard_data = validated_data.pop('yard')
        sprinkler_heads_data = validated_data.pop('sprinkler_heads', [])
        sketch_elements_data = validated_data.pop('sketch_elements', [])

        # Create Project
        project = Project.objects.create(user=user, **project_data)

        # Create Yard
        yard = Yard.objects.create(project=project, **yard_data)

        # Create a default Zone
        zone = Zone.objects.create(yard=yard, zone_number=1)

        # Create Sprinkler Heads
        for sh_data in sprinkler_heads_data:
            SprinklerHead.objects.create(zone=zone, **sh_data)

        # Create Sketch Elements
        for se_data in sketch_elements_data:
            SketchElement.objects.create(yard=yard, **se_data)

        return project
