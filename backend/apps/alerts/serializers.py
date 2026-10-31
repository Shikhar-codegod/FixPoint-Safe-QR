from rest_framework import serializers
from .models import AlertRecord, AlertStatus, AlertSeverity, AlertEvidence, AlertConfirmationToken

class AlertPublicSerializer(serializers.ModelSerializer):
    """
    Public-safe representation of an alert.
    Never exposes customer name, email, phone number, medical info, or emergency contacts.
    """
    vehicle_registration = serializers.CharField(source='qr_badge.vehicle_registration', read_only=True)
    vehicle_model = serializers.CharField(source='qr_badge.vehicle_model', read_only=True)

    class Meta:
        model = AlertRecord
        fields = [
            'id',
            'status',
            'severity',
            'vehicle_registration',
            'vehicle_model',
            'created_at',
            'confirmed_at',
        ]
        read_only_fields = fields


class AlertDetailSerializer(serializers.ModelSerializer):
    """
    Full detail representation for authorized users (owner, operators, supervisors, admins).
    """
    user_email = serializers.EmailField(source='user.email', read_only=True, default=None)
    qr_code_identifier = serializers.CharField(source='qr_badge.code_identifier', read_only=True, default=None)
    vehicle_registration = serializers.CharField(source='qr_badge.vehicle_registration', read_only=True, default=None)
    vehicle_model = serializers.CharField(source='qr_badge.vehicle_model', read_only=True, default=None)
    claimed_by_email = serializers.EmailField(source='claimed_by.email', read_only=True, default=None)
    closed_by_email = serializers.EmailField(source='closed_by.email', read_only=True, default=None)

    class Meta:
        model = AlertRecord
        fields = [
            'id',
            'user_email',
            'qr_code_identifier',
            'vehicle_registration',
            'vehicle_model',
            'status',
            'severity',
            'latitude',
            'longitude',
            'location_address',
            'notes',
            'claimed_by_email',
            'closed_by_email',
            'confirmed_at',
            'activated_at',
            'closed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user_email',
            'qr_code_identifier',
            'vehicle_registration',
            'vehicle_model',
            'claimed_by_email',
            'closed_by_email',
            'confirmed_at',
            'activated_at',
            'closed_at',
            'created_at',
            'updated_at',
        ]


# Backward compatibility alias
AlertRecordSerializer = AlertDetailSerializer


class AlertDraftCreateSerializer(serializers.Serializer):
    qr_token = serializers.CharField(max_length=128, required=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    location_address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    severity = serializers.ChoiceField(choices=AlertSeverity.choices, default=AlertSeverity.CRITICAL)


class AlertConfirmSerializer(serializers.Serializer):
    confirmation_token = serializers.CharField(max_length=128, required=True)


class AlertCloseSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True)


class AlertEvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertEvidence
        fields = ['id', 'alert', 'file_url', 'caption', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
