"""
Test Suite: FixPoint Drive Safe-QR SOS Backend Foundation

Covers:
  1. Django project startup (settings load, installed apps, URL resolution)
  2. Database connectivity
  3. JWT authentication (obtain token, refresh, invalid credentials)
  4. Protected endpoint requires authentication
  5. Role-based permission checks
  6. Health-check endpoint
"""
import pytest
from django.test import TestCase
from django.urls import reverse, resolve
from django.db import connection
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import CustomUser, UserRole

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_user(email, password, role=UserRole.CUSTOMER, **kwargs):
    return CustomUser.objects.create_user(email=email, password=password, role=role, **kwargs)


# ---------------------------------------------------------------------------
# 1. Django Project Startup
# ---------------------------------------------------------------------------

class TestDjangoStartup(TestCase):
    """Verifies the project loads correctly with all required apps installed."""

    def test_django_settings_loaded(self):
        assert hasattr(settings, 'INSTALLED_APPS'), "INSTALLED_APPS must be defined"

    def test_required_apps_installed(self):
        """
        Checks that all required apps are installed.
        Django normalises AppConfig entries so we check both the raw string
        and the short app_label via the app registry.
        """
        from django.apps import apps as django_app_registry

        # Required app labels (the `name` attr of each AppConfig)
        required_app_names = [
            'apps.accounts',
            'apps.profiles',
            'apps.qr_codes',
            'apps.contacts',
            'apps.alerts',
            'apps.notifications',
            'apps.incidents',
            'apps.responders',
            'apps.medical',
            'apps.operations',
            'apps.audit',
            'apps.common',
            'rest_framework',
            'rest_framework_simplejwt',
            'corsheaders',
            'drf_spectacular',
        ]
        installed_names = {cfg.name for cfg in django_app_registry.get_app_configs()}
        for app_name in required_app_names:
            assert app_name in installed_names, (
                f"App '{app_name}' is not installed. "
                f"Registered apps: {sorted(installed_names)}"
            )

    def test_auth_user_model(self):
        assert settings.AUTH_USER_MODEL == 'accounts.CustomUser'

    def test_health_check_url_resolves(self):
        url = reverse('common:health-check')
        assert url == '/api/v1/health/'

    def test_auth_token_url_resolves(self):
        url = reverse('accounts:token_obtain_pair')
        assert url == '/api/v1/auth/token/'

    def test_register_url_resolves(self):
        url = reverse('accounts:register')
        assert url == '/api/v1/auth/register/'


# ---------------------------------------------------------------------------
# 2. Database Connectivity
# ---------------------------------------------------------------------------

class TestDatabaseConnectivity(TestCase):
    """Verifies Django can execute queries against the configured database."""

    def test_database_is_reachable(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
        assert row is not None
        assert row[0] == 1

    def test_custom_user_table_exists(self):
        """Creating a user exercises the ORM and the accounts_customuser table."""
        user = create_user('db_test@fixpoint.io', 'SecurePass!123')
        assert user.pk is not None
        assert CustomUser.objects.filter(email='db_test@fixpoint.io').exists()

    def test_custom_user_uuid_pk(self):
        user = create_user('uuid_test@fixpoint.io', 'SecurePass!123')
        import uuid
        assert isinstance(user.id, uuid.UUID)


# ---------------------------------------------------------------------------
# 3. JWT Authentication
# ---------------------------------------------------------------------------

class TestJWTAuthentication(TestCase):
    """Verifies JWT token obtain and refresh flows."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='jwt_user@fixpoint.io',
            password='JwtTestPass!2026',
            first_name='JWT',
            last_name='User'
        )
        self.token_url = reverse('accounts:token_obtain_pair')
        self.refresh_url = reverse('accounts:token_refresh')

    def test_obtain_token_pair_success(self):
        response = self.client.post(self.token_url, {
            'email': 'jwt_user@fixpoint.io',
            'password': 'JwtTestPass!2026'
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'access' in data
        assert 'refresh' in data

    def test_token_contains_user_metadata(self):
        response = self.client.post(self.token_url, {
            'email': 'jwt_user@fixpoint.io',
            'password': 'JwtTestPass!2026'
        })
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert 'user' in data
        assert data['user']['email'] == 'jwt_user@fixpoint.io'
        assert data['user']['role'] == UserRole.CUSTOMER

    def test_refresh_token_returns_new_access(self):
        # Step 1: Obtain initial tokens
        resp1 = self.client.post(self.token_url, {
            'email': 'jwt_user@fixpoint.io',
            'password': 'JwtTestPass!2026'
        })
        refresh_token = resp1.json()['refresh']

        # Step 2: Refresh access token
        resp2 = self.client.post(self.refresh_url, {'refresh': refresh_token})
        assert resp2.status_code == status.HTTP_200_OK
        assert 'access' in resp2.json()


# ---------------------------------------------------------------------------
# 4. Invalid Authentication
# ---------------------------------------------------------------------------

class TestInvalidAuthentication(TestCase):
    """Verifies that invalid credentials are correctly rejected."""

    def setUp(self):
        self.client = APIClient()
        self.token_url = reverse('accounts:token_obtain_pair')
        create_user('existing@fixpoint.io', 'ValidPass!2026')

    def test_wrong_password_rejected(self):
        response = self.client.post(self.token_url, {
            'email': 'existing@fixpoint.io',
            'password': 'WRONG_PASSWORD'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_nonexistent_user_rejected(self):
        response = self.client.post(self.token_url, {
            'email': 'ghost@fixpoint.io',
            'password': 'AnyPassword!1'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_email_rejected(self):
        response = self.client.post(self.token_url, {'password': 'AnyPassword!1'})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_protected_endpoint_without_token(self):
        """Accessing /api/v1/auth/me/ without auth returns 401."""
        response = self.client.get(reverse('accounts:current_user'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_protected_endpoint_with_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer INVALID.TOKEN.HERE')
        response = self.client.get(reverse('accounts:current_user'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# 5. Role-Based Permission Checks
# ---------------------------------------------------------------------------

class TestRoleBasedPermissions(TestCase):
    """Verifies permission classes correctly gate access by role."""

    def setUp(self):
        self.client = APIClient()
        self.token_url = reverse('accounts:token_obtain_pair')

        self.customer = create_user('cust@fixpoint.io', 'TestPass!2026', role=UserRole.CUSTOMER)
        self.supervisor = create_user(
            'sup@fixpoint.io', 'TestPass!2026',
            role=UserRole.SUPERVISOR,
            is_staff=True
        )
        self.police = create_user('police@fixpoint.io', 'TestPass!2026', role=UserRole.POLICE_RESPONDER)

    def _get_token(self, email, password):
        resp = self.client.post(self.token_url, {'email': email, 'password': password})
        return resp.json().get('access')

    def test_customer_can_access_me_endpoint(self):
        token = self._get_token('cust@fixpoint.io', 'TestPass!2026')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.get(reverse('accounts:current_user'))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()['data']['role'] == UserRole.CUSTOMER

    def test_customer_cannot_access_audit_events(self):
        """Audit events endpoint requires SUPERVISOR or ADMIN."""
        token = self._get_token('cust@fixpoint.io', 'TestPass!2026')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.get(reverse('audit:audit-events-list'))
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_supervisor_can_access_audit_events(self):
        token = self._get_token('sup@fixpoint.io', 'TestPass!2026')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.get(reverse('audit:audit-events-list'))
        assert resp.status_code == status.HTTP_200_OK

    def test_customer_cannot_access_responder_dispatches(self):
        token = self._get_token('cust@fixpoint.io', 'TestPass!2026')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.get(reverse('responders:responder-dispatches'))
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_police_responder_can_access_dispatches(self):
        token = self._get_token('police@fixpoint.io', 'TestPass!2026')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.get(reverse('responders:responder-dispatches'))
        assert resp.status_code == status.HTTP_200_OK

    def test_responder_is_not_auto_verified(self):
        """Selecting a responder role must never auto-verify the responder."""
        assert self.police.is_verified_responder is False

    def test_customer_cannot_access_operations_log(self):
        token = self._get_token('cust@fixpoint.io', 'TestPass!2026')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.get(reverse('operations:operations-log'))
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_supervisor_can_access_operations_log(self):
        token = self._get_token('sup@fixpoint.io', 'TestPass!2026')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.get(reverse('operations:operations-log'))
        assert resp.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# 6. Health Check Endpoint
# ---------------------------------------------------------------------------

class TestHealthCheckEndpoint(TestCase):
    """Verifies the health-check responds correctly without exposing internals."""

    def setUp(self):
        self.client = APIClient()
        self.health_url = reverse('common:health-check')

    def test_health_check_returns_200(self):
        response = self.client.get(self.health_url)
        assert response.status_code == status.HTTP_200_OK

    def test_health_check_does_not_require_auth(self):
        """Health check must be publicly accessible."""
        response = self.client.get(self.health_url)
        assert response.status_code != status.HTTP_401_UNAUTHORIZED

    def test_health_check_response_structure(self):
        response = self.client.get(self.health_url)
        data = response.json()
        assert 'status' in data
        assert 'version' in data
        assert 'services' in data
        assert 'database' in data['services']

    def test_health_check_shows_database_operational(self):
        response = self.client.get(self.health_url)
        data = response.json()
        assert data['services']['database'] == 'operational'

    def test_health_check_does_not_expose_db_credentials(self):
        response = self.client.get(self.health_url)
        raw = response.content.decode()
        assert 'postgres://' not in raw
        assert 'PASSWORD' not in raw
        assert 'SECRET' not in raw


# ---------------------------------------------------------------------------
# 7. User Registration
# ---------------------------------------------------------------------------

class TestUserRegistration(TestCase):
    """Verifies the registration flow and role constraints."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('accounts:register')

    def test_customer_registration_succeeds(self):
        payload = {
            'email': 'newcustomer@fixpoint.io',
            'password': 'SecurePass!2026',
            'password_confirm': 'SecurePass!2026',
            'first_name': 'Test',
            'last_name': 'Customer',
            'role': UserRole.CUSTOMER,
        }
        resp = self.client.post(self.register_url, payload)
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data['data']['email'] == 'newcustomer@fixpoint.io'
        assert data['data']['is_verified_responder'] is False

    def test_password_mismatch_rejected(self):
        payload = {
            'email': 'mismatch@fixpoint.io',
            'password': 'SecurePass!2026',
            'password_confirm': 'DIFFERENT_PASS',
            'first_name': 'Bad',
            'last_name': 'Request',
            'role': UserRole.CUSTOMER,
        }
        resp = self.client.post(self.register_url, payload)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_admin_self_registration_blocked(self):
        payload = {
            'email': 'badactor@fixpoint.io',
            'password': 'SecurePass!2026',
            'password_confirm': 'SecurePass!2026',
            'first_name': 'Bad',
            'last_name': 'Actor',
            'role': UserRole.ADMIN,
        }
        resp = self.client.post(self.register_url, payload)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_police_responder_registers_unverified(self):
        payload = {
            'email': 'officer@fixpoint.io',
            'password': 'SecurePass!2026',
            'password_confirm': 'SecurePass!2026',
            'first_name': 'Officer',
            'last_name': 'Smith',
            'role': UserRole.POLICE_RESPONDER,
        }
        resp = self.client.post(self.register_url, payload)
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()['data']['is_verified_responder'] is False
