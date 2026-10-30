from rest_framework import serializers
from .models import AuditEvent

class AuditEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source='actor.email', read_only=True)

    class Meta:
        model = AuditEvent
        fields = [
            'id',
            'actor_email',
            'action',
            'ip_address',
            'user_agent',
            'target_model',
            'target_id',
            'payload',
            'timestamp',
        ]
        read_only_fields = fields
