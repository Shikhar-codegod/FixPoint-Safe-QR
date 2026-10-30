from rest_framework import serializers
from .models import EmergencyContact, ConsentStatus, PreferredLanguage
from .utils import normalize_phone_number, compute_phone_hash

class EmergencyContactSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=32)
    email = serializers.EmailField(required=False, allow_blank=True, default='')

    class Meta:
        model = EmergencyContact
        fields = [
            'id',
            'name',
            'relationship',
            'phone_number',
            'email',
            'priority_order',
            'is_primary',
            'consent_status',
            'consent_given_at',
            'consent_withdrawn_at',
            'preferred_language',
            'notify_whatsapp',
            'notify_sms',
            'notify_call',
            'wave',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'consent_status',
            'consent_given_at',
            'consent_withdrawn_at',
            'created_at',
            'updated_at'
        ]

    def validate_phone_number(self, value):
        try:
            return normalize_phone_number(value)
        except ValueError as err:
            raise serializers.ValidationError(str(err))

    def validate(self, attrs):
        user = self.context.get('request').user if self.context.get('request') else None
        
        # In updates, if user is not in context, fall back to instance.user
        if not user and self.instance:
            user = self.instance.user

        phone_number = attrs.get('phone_number')
        if phone_number and user:
            phone_hash = compute_phone_hash(phone_number)
            qs = EmergencyContact.objects.filter(user=user, phone_hash=phone_hash)
            if self.instance:
                qs = qs.exclude(id=self.instance.id)
            if qs.exists():
                raise serializers.ValidationError(
                    {"phone_number": "An emergency contact with this phone number already exists for your account."}
                )

        # Enforce max 5 contacts per user during creation
        if not self.instance and user:
            count = EmergencyContact.objects.filter(user=user).count()
            if count >= 5:
                raise serializers.ValidationError(
                    {"non_field_errors": ["Maximum 5 emergency contacts permitted per user."]}
                )

        return attrs

class ConsentDecisionSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=['accept', 'decline'])
