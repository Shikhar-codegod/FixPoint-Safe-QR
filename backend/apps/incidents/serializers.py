from rest_framework import serializers
from .models import IncidentRecord, IncidentType, IncidentPriority, LocationPrecision, IncidentPhoto

class IncidentPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentPhoto
        fields = [
            'id',
            'file_size',
            'content_type',
            'created_at',
        ]
        read_only_fields = ['id', 'file_size', 'content_type', 'created_at']

class IncidentRecordSerializer(serializers.ModelSerializer):
    reporter_email = serializers.EmailField(source='reporter.email', read_only=True, allow_null=True)
    claimed_by_email = serializers.EmailField(source='claimed_by.email', read_only=True, allow_null=True)
    incident_type = serializers.ChoiceField(choices=IncidentType.choices)
    priority = serializers.ChoiceField(choices=IncidentPriority.choices, default=IncidentPriority.LOW)
    location_precision = serializers.ChoiceField(choices=LocationPrecision.choices, default=LocationPrecision.NONE)
    description = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    location_address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    photos = IncidentPhotoSerializer(many=True, read_only=True)
    qr_code_identifier = serializers.CharField(source='qr_badge.code_identifier', read_only=True, allow_null=True)

    class Meta:
        model = IncidentRecord
        fields = [
            'id',
            'incident_number',
            'incident_type',
            'status',
            'priority',
            'location_precision',
            'reporter_contact_shared',
            'reporter_email',
            'claimed_by_email',
            'qr_code_identifier',
            'latitude',
            'longitude',
            'location_address',
            'description',
            'operator_notes',
            'photos',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'incident_number', 'created_at', 'updated_at']

    def validate(self, attrs):
        lat = attrs.get('latitude')
        lng = attrs.get('longitude')

        if (lat is not None and lng is None) or (lat is None and lng is not None):
            raise serializers.ValidationError(
                {"location": "Both latitude and longitude must be provided together, or both omitted."}
            )

        if lat is not None:
            if not (-90.0 <= float(lat) <= 90.0):
                raise serializers.ValidationError(
                    {"latitude": "Latitude must be between -90.0 and +90.0 degrees."}
                )
        if lng is not None:
            if not (-180.0 <= float(lng) <= 180.0):
                raise serializers.ValidationError(
                    {"longitude": "Longitude must be between -180.0 and +180.0 degrees."}
                )

        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if not request or not request.user or not request.user.is_authenticated:
            # Public / anonymous view: hide reporter details
            if not instance.reporter_contact_shared:
                data['reporter_email'] = None
            return data

        user = request.user
        is_staff = user.role in ['OPERATOR', 'SUPERVISOR', 'ADMIN'] or user.is_staff
        is_reporter = instance.reporter_id == user.id
        
        # QR badge owner viewing an incident reported on their badge
        is_badge_owner = instance.qr_badge and instance.qr_badge.user_id == user.id

        if not is_staff and not is_reporter:
            if is_badge_owner and not instance.reporter_contact_shared:
                data['reporter_email'] = None

        return data
