from rest_framework import serializers
from .models import OperationsLogEntry

class OperationsLogEntrySerializer(serializers.ModelSerializer):
    operator_email = serializers.EmailField(source='operator.email', read_only=True)
    incident_number = serializers.CharField(source='incident.incident_number', read_only=True, default=None)

    class Meta:
        model = OperationsLogEntry
        fields = [
            'id',
            'operator_email',
            'incident_number',
            'action',
            'details',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
