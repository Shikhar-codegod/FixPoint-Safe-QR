from rest_framework import serializers
from .models import IncidentRecord

class IncidentRecordSerializer(serializers.ModelSerializer):
    reporter_email = serializers.EmailField(source='reporter.email', read_only=True)

    class Meta:
        model = IncidentRecord
        fields = [
            'id',
            'incident_number',
            'incident_type',
            'status',
            'reporter_email',
            'latitude',
            'longitude',
            'location_address',
            'description',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'incident_number', 'created_at', 'updated_at']
