import io
import pytest
from PIL import Image
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import CustomUser, UserRole
from apps.qr_codes.models import QRCodeBadge, QRCodeStatus
from apps.incidents.models import IncidentRecord, IncidentType, IncidentPriority, IncidentStatus, IncidentPhoto
from apps.notifications.models import ContactNotificationChain
from apps.alerts.models import AlertRecord

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def customer(db):
    return CustomUser.objects.create_user(
        email='car_owner@fixpoint.io',
        password='TestPassword!123',
        first_name='Karan',
        last_name='Mehta',
        role=UserRole.CUSTOMER
    )

@pytest.fixture
def operator(db):
    return CustomUser.objects.create_user(
        email='operator@fixpoint.io',
        password='TestPassword!123',
        first_name='Ops',
        last_name='Desk',
        role=UserRole.OPERATOR
    )

@pytest.fixture
def active_qr(db, customer):
    return QRCodeBadge.objects.create(
        user=customer,
        code_identifier='FP-SAFE-TEST-001',
        vehicle_registration='MH02AB1234',
        vehicle_model='Honda City',
        status=QRCodeStatus.ACTIVE
    )

@pytest.fixture
def revoked_qr(db, customer):
    return QRCodeBadge.objects.create(
        user=customer,
        code_identifier='FP-SAFE-REVOKED-002',
        vehicle_registration='MH02CD5678',
        status=QRCodeStatus.REVOKED
    )

def create_test_image(format='JPEG', with_exif=True):
    img = Image.new('RGB', (100, 100), color='red')
    out = io.BytesIO()
    if with_exif and format == 'JPEG':
        exif = img.getexif()
        exif[0x010e] = "FixPoint Test EXIF Title"
        img.save(out, format=format, exif=exif)
    else:
        img.save(out, format=format)
    out.seek(0)
    return SimpleUploadedFile(f"test_image.{format.lower()}", out.getvalue(), content_type=f"image/{format.lower()}")

@pytest.mark.django_db
class TestIncidentReporting:
    def test_all_five_categories_supported(self, customer):
        client = APIClient()
        client.force_authenticate(user=customer)
        url = reverse('incidents:incidents-list-create')
        categories = ['ACCIDENT', 'DAMAGE', 'TAMPERING', 'HAZARD', 'OTHER']
        for cat in categories:
            res = client.post(url, {
                'incident_type': cat,
                'description': f'Reporting a {cat} incident.'
            })
            assert res.status_code == status.HTTP_201_CREATED
            assert res.json()['data']['incident_type'] == cat

    def test_invalid_category_rejected(self, customer):
        client = APIClient()
        client.force_authenticate(user=customer)
        url = reverse('incidents:incidents-list-create')
        res = client.post(url, {
            'incident_type': 'INVALID_CATEGORY',
            'description': 'Invalid test'
        })
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_coordinate_validation(self, customer):
        client = APIClient()
        client.force_authenticate(user=customer)
        url = reverse('incidents:incidents-list-create')

        # One coordinate provided without the other: rejected
        res_lat_only = client.post(url, {
            'incident_type': 'ACCIDENT',
            'latitude': 19.0760
        })
        assert res_lat_only.status_code == status.HTTP_400_BAD_REQUEST

        # Out-of-bounds latitude rejected
        res_bad_lat = client.post(url, {
            'incident_type': 'ACCIDENT',
            'latitude': 95.0,
            'longitude': 72.8777
        })
        assert res_bad_lat.status_code == status.HTTP_400_BAD_REQUEST

        # Out-of-bounds longitude rejected
        res_bad_lng = client.post(url, {
            'incident_type': 'ACCIDENT',
            'latitude': 19.0760,
            'longitude': 190.0
        })
        assert res_bad_lng.status_code == status.HTTP_400_BAD_REQUEST

        # Valid coordinates: accepted
        res_valid = client.post(url, {
            'incident_type': 'ACCIDENT',
            'latitude': 19.0760,
            'longitude': 72.8777
        })
        assert res_valid.status_code == status.HTTP_201_CREATED

    def test_location_and_photos_optional(self, customer):
        client = APIClient()
        client.force_authenticate(user=customer)
        url = reverse('incidents:incidents-list-create')
        res = client.post(url, {
            'incident_type': 'HAZARD',
            'description': 'Oil spill on road'
        })
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()['data']
        assert data['latitude'] is None
        assert data['longitude'] is None
        assert data['photos'] == []

    def test_public_qr_incident_reporting(self, active_qr, revoked_qr):
        client = APIClient()
        url_active = reverse('incidents:incident-public-report', kwargs={'code_identifier': active_qr.code_identifier})
        res = client.post(url_active, {
            'incident_type': 'DAMAGE',
            'description': 'Scratched bumper in parking'
        })
        assert res.status_code == status.HTTP_201_CREATED
        assert res.json()['data']['qr_code_identifier'] == active_qr.code_identifier

        # Revoked QR badge report is rejected with 404
        url_revoked = reverse('incidents:incident-public-report', kwargs={'code_identifier': revoked_qr.code_identifier})
        res_rev = client.post(url_revoked, {
            'incident_type': 'DAMAGE',
            'description': 'Should fail'
        })
        assert res_rev.status_code == status.HTTP_404_NOT_FOUND

    def test_security_separation_incident_creates_zero_notification_chains(self, customer, active_qr):
        """CRITICAL: Incidents must NEVER trigger contact notification chains or alerts."""
        client = APIClient()
        client.force_authenticate(user=customer)
        initial_chain_count = ContactNotificationChain.objects.count()
        initial_alert_count = AlertRecord.objects.count()

        url = reverse('incidents:incidents-list-create')
        res = client.post(url, {
            'incident_type': 'ACCIDENT',
            'description': 'Minor fender bender'
        })
        assert res.status_code == status.HTTP_201_CREATED

        final_chain_count = ContactNotificationChain.objects.count()
        final_alert_count = AlertRecord.objects.count()
        assert final_chain_count == initial_chain_count == 0
        assert final_alert_count == initial_alert_count

    def test_non_operator_cannot_patch_incident_status(self, customer, operator):
        client = APIClient()
        client.force_authenticate(user=customer)
        create_res = client.post(reverse('incidents:incidents-list-create'), {
            'incident_type': 'TAMPERING',
            'description': 'Mirror bent'
        })
        inc_number = create_res.json()['data']['incident_number']
        detail_url = reverse('incidents:incident-detail', kwargs={'incident_number': inc_number})

        # Regular customer cannot PATCH status (returns 403)
        patch_res = client.patch(detail_url, {'status': IncidentStatus.RESOLVED})
        assert patch_res.status_code == status.HTTP_403_FORBIDDEN

        # Operator CAN PATCH status
        op_client = APIClient()
        op_client.force_authenticate(user=operator)
        op_res = op_client.patch(detail_url, {'status': IncidentStatus.IN_PROGRESS})
        assert op_res.status_code == status.HTTP_200_OK
        assert op_res.json()['data']['status'] == IncidentStatus.IN_PROGRESS

    def test_operator_queue_access(self, customer, operator):
        queue_url = reverse('incidents:incident-queue')

        # Customer gets 403 on queue
        client = APIClient()
        client.force_authenticate(user=customer)
        assert client.get(queue_url).status_code == status.HTTP_403_FORBIDDEN

        # Operator gets 200 on queue
        op_client = APIClient()
        op_client.force_authenticate(user=operator)
        res = op_client.get(queue_url)
        assert res.status_code == status.HTTP_200_OK

    def test_reporter_contact_shared_privacy(self, customer, active_qr, operator):
        reporter_user = CustomUser.objects.create_user(
            email='reporter_citizen@fixpoint.io',
            password='TestPassword!123',
            role=UserRole.PUBLIC
        )
        reporter_client = APIClient()
        reporter_client.force_authenticate(user=reporter_user)
        report_url = reverse('incidents:incident-public-report', kwargs={'code_identifier': active_qr.code_identifier})

        # Case 1: reporter_contact_shared is False
        res1 = reporter_client.post(report_url, {
            'incident_type': 'DAMAGE',
            'description': 'Mirror broken',
            'reporter_contact_shared': False
        })
        assert res1.status_code == status.HTTP_201_CREATED
        inc1_num = res1.json()['data']['incident_number']

        # QR owner views incident: reporter_email must be hidden (None)
        owner_client = APIClient()
        owner_client.force_authenticate(user=customer)
        view_res1 = owner_client.get(reverse('incidents:incident-detail', kwargs={'incident_number': inc1_num}))
        assert view_res1.status_code == status.HTTP_200_OK
        assert view_res1.json()['data']['reporter_email'] is None

        # Operator views incident: reporter_email is visible
        op_client = APIClient()
        op_client.force_authenticate(user=operator)
        op_view1 = op_client.get(reverse('incidents:incident-detail', kwargs={'incident_number': inc1_num}))
        assert op_view1.status_code == status.HTTP_200_OK
        assert op_view1.json()['data']['reporter_email'] == 'reporter_citizen@fixpoint.io'

    def test_photo_upload_exif_stripped_and_limits(self, customer):
        client = APIClient()
        client.force_authenticate(user=customer)
        create_res = client.post(reverse('incidents:incidents-list-create'), {
            'incident_type': 'ACCIDENT',
            'description': 'Photo test'
        })
        inc_num = create_res.json()['data']['incident_number']
        photo_url = reverse('incidents:incident-photos', kwargs={'incident_number': inc_num})

        # Upload 1: Valid JPEG with EXIF
        img1 = create_test_image('JPEG', with_exif=True)
        res1 = client.post(photo_url, {'photo': img1}, format='multipart')
        assert res1.status_code == status.HTTP_201_CREATED
        photo_id = res1.json()['data']['id']

        # Verify EXIF is stripped from saved file
        saved_photo = IncidentPhoto.objects.get(id=photo_id)
        with saved_photo.photo_file.open('rb') as f:
            saved_img = Image.open(f)
            exif_data = saved_img.getexif()
            assert len(exif_data) == 0

        # Upload 2 & 3: Valid images
        img2 = create_test_image('PNG')
        img3 = create_test_image('WEBP')
        assert client.post(photo_url, {'photo': img2}, format='multipart').status_code == status.HTTP_201_CREATED
        assert client.post(photo_url, {'photo': img3}, format='multipart').status_code == status.HTTP_201_CREATED

        # Upload 4: Exceeds max 3 photos -> rejected
        img4 = create_test_image('JPEG')
        res4 = client.post(photo_url, {'photo': img4}, format='multipart')
        assert res4.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Maximum 3 photos' in str(res4.json())

        # Non-image upload rejected
        bad_file = SimpleUploadedFile("fake.txt", b"not an image", content_type="text/plain")
        res_bad = client.post(photo_url, {'photo': bad_file}, format='multipart')
        assert res_bad.status_code == status.HTTP_400_BAD_REQUEST

    def test_upgrade_incident_to_alert(self, customer, operator, active_qr, django_capture_on_commit_callbacks):
        from apps.contacts.models import EmergencyContact, ConsentStatus
        from apps.contacts.utils import compute_phone_hash

        # Add an emergency contact for the vehicle owner
        EmergencyContact.objects.create(
            user=customer,
            name='Emergency Contact',
            phone_number='+919876543210',
            phone_hash=compute_phone_hash('+919876543210'),
            consent_status=ConsentStatus.GRANTED,
        )

        client = APIClient()
        client.force_authenticate(user=customer)
        create_res = client.post(reverse('incidents:incidents-list-create'), {
            'incident_type': 'ACCIDENT',
            'qr_code_identifier': active_qr.code_identifier,
            'description': 'Serious crash requiring immediate response',
            'latitude': '19.076000',
            'longitude': '72.877700'
        })
        assert create_res.status_code == status.HTTP_201_CREATED
        inc_num = create_res.json()['data']['incident_number']
        upgrade_url = reverse('incidents:incident-upgrade-to-alert', kwargs={'incident_number': inc_num})

        # Regular customer cannot upgrade incident
        cust_res = client.post(upgrade_url)
        assert cust_res.status_code == status.HTTP_403_FORBIDDEN

        # Operator upgrades incident to emergency alert
        op_client = APIClient()
        op_client.force_authenticate(user=operator)
        with django_capture_on_commit_callbacks(execute=True):
            op_res = op_client.post(upgrade_url)
        assert op_res.status_code == status.HTTP_201_CREATED
        data = op_res.json()['data']
        assert data['incident_number'] == inc_num
        assert data['alert_severity'] == 'HIGH'
        alert_id = data['alert_id']

        # Verify incident and alert are linked in DB
        incident = IncidentRecord.objects.get(incident_number=inc_num)
        assert incident.alert is not None
        assert str(incident.alert.id) == alert_id
        assert incident.alert.severity == 'HIGH'

        # Verify contact notification chain was created for the vehicle owner
        chains = ContactNotificationChain.objects.filter(alert=incident.alert)
        assert chains.count() == 1
        assert chains.first().contact.user == customer

        # Attempting to upgrade again returns 400
        repeat_res = op_client.post(upgrade_url)
        assert repeat_res.status_code == status.HTTP_400_BAD_REQUEST

