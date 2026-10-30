from rest_framework import serializers
from .models import MedicalProfile

class MedicalProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = MedicalProfile
        fields = [
            'id',
            'user_email',
            'blood_group',
            'allergies',
            'medications',
            'chronic_conditions',
            'emergency_notes',
            'organ_donor',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
