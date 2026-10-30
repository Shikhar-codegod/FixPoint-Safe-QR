from apps.audit.services import log_audit_event
from .models import MedicalProfile

def get_or_create_medical_profile(user) -> MedicalProfile:
    profile, created = MedicalProfile.objects.get_or_create(user=user)
    if created:
        log_audit_event(
            action='MEDICAL_PROFILE_CREATED',
            actor=user,
            target_model='MedicalProfile',
            target_id=str(profile.id)
        )
    return profile

def update_medical_profile(user, **data) -> MedicalProfile:
    profile = get_or_create_medical_profile(user)
    for field in ['blood_group', 'allergies', 'medications', 'chronic_conditions', 'emergency_notes', 'organ_donor']:
        if field in data:
            setattr(profile, field, data[field])
    profile.save()
    log_audit_event(
        action='MEDICAL_PROFILE_UPDATED',
        actor=user,
        target_model='MedicalProfile',
        target_id=str(profile.id),
        payload={'blood_group': profile.blood_group, 'organ_donor': profile.organ_donor}
    )
    return profile
