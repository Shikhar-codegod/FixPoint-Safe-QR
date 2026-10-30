from rest_framework import serializers
from .models import UserProfile, ResponderProfile

class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'role',
            'avatar_url',
            'address',
            'city',
            'preferred_language',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ResponderProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)

    class Meta:
        model = ResponderProfile
        fields = [
            'id',
            'email',
            'full_name',
            'role',
            'badge_number',
            'agency_name',
            'service_jurisdiction',
            'verification_status',
            'verified_at',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'verification_status', 'verified_at', 'created_at', 'updated_at']
