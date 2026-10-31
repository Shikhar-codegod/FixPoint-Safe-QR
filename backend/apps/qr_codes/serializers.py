from rest_framework import serializers
from .models import QRCodeBadge

class QRCodeBadgeSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = QRCodeBadge
        fields = [
            'id',
            'owner_email',
            'code_identifier',
            'generation',
            'vehicle_registration',
            'vehicle_model',
            'status',
            'scan_count',
            'last_scanned_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'generation', 'scan_count', 'last_scanned_at', 'created_at', 'updated_at']
