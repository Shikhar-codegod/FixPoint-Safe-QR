from rest_framework import serializers
from .models import NotificationRecord

class NotificationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationRecord
        fields = [
            'id',
            'recipient_destination',
            'channel',
            'title',
            'body',
            'status',
            'error_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'error_message', 'created_at', 'updated_at']
