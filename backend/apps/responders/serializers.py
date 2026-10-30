from rest_framework import serializers
from .models import ResponderDispatch

class ResponderDispatchSerializer(serializers.ModelSerializer):
    responder_email = serializers.EmailField(source='responder.email', read_only=True)
    incident_number = serializers.CharField(source='incident.incident_number', read_only=True)

    class Meta:
        model = ResponderDispatch
        fields = [
            'id',
            'responder_email',
            'incident_number',
            'status',
            'assigned_at',
            'arrived_at',
            'completed_at',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'assigned_at', 'created_at', 'updated_at']
