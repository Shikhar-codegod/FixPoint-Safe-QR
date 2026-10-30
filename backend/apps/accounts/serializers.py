from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser, UserRole

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends Simple JWT token serializer to include user identity and role claims in token payload.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        token['is_verified_responder'] = user.is_verified_responder
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'is_verified_responder': self.user.is_verified_responder,
        }
        return data

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'password',
            'password_confirm',
            'first_name',
            'last_name',
            'phone_number',
            'role',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        
        # Public users and Customers can register directly.
        # Responder roles can be registered but will require subsequent verification.
        role = attrs.get('role', UserRole.CUSTOMER)
        if role in [UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.OPERATOR]:
            raise serializers.ValidationError({
                'role': 'Privileged administrative roles cannot be self-registered.'
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        return CustomUser.objects.create_user(password=password, **validated_data)

class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'phone_number',
            'role',
            'is_verified_responder',
            'created_at',
        ]
        read_only_fields = fields
