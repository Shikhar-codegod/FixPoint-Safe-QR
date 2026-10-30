from rest_framework import serializers
from .models import AlertRecord

class AlertRecordSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    qr_code_identifier = serializers.CharField(source='qr_badge.code_identifier', read_only=True)

    class Meta:
        model = AlertRecord
        fields = [
            'id',
            'user_email',
            'qr_code_identifier',
            'status',
            'severity',
            'latitude',
            'longitude',
            'location_address',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
