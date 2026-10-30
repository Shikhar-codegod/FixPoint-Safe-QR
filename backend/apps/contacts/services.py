from django.db import transaction
from apps.audit.services import log_audit_event
from .models import EmergencyContact

def create_emergency_contact(
    user,
    name: str,
    relationship: str,
    phone_number: str,
    email: str = '',
    priority_order: int = 1,
    is_primary: bool = False
) -> EmergencyContact:
    with transaction.atomic():
        if is_primary:
            EmergencyContact.objects.filter(user=user, is_primary=True).update(is_primary=False)
        contact = EmergencyContact.objects.create(
            user=user,
            name=name,
            relationship=relationship,
            phone_number=phone_number,
            email=email,
            priority_order=priority_order,
            is_primary=is_primary
        )
        log_audit_event(
            action='EMERGENCY_CONTACT_CREATED',
            actor=user,
            target_model='EmergencyContact',
            target_id=str(contact.id),
            payload={'name': name, 'relationship': relationship}
        )
    return contact

def delete_emergency_contact(contact: EmergencyContact, user) -> None:
    contact_id = str(contact.id)
    contact.delete()
    log_audit_event(
        action='EMERGENCY_CONTACT_DELETED',
        actor=user,
        target_model='EmergencyContact',
        target_id=contact_id
    )
