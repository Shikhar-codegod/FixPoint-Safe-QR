import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from apps.common.models import TimeStampedModel

class UserRole(models.TextChoices):
    CUSTOMER = 'CUSTOMER', 'Customer'
    PUBLIC = 'PUBLIC', 'Public Citizen'
    POLICE_RESPONDER = 'POLICE_RESPONDER', 'Police Responder'
    MEDICAL_RESPONDER = 'MEDICAL_RESPONDER', 'Medical Responder'
    OPERATOR = 'OPERATOR', 'Emergency Operator'
    SUPERVISOR = 'SUPERVISOR', 'Command Supervisor'
    ADMIN = 'ADMIN', 'System Administrator'

class CustomUserManager(BaseUserManager):
    """
    Manager for CustomUser using email as the unique username identifier.
    """
    def create_user(self, email, password=None, role=UserRole.CUSTOMER, **extra_fields):
        if not email:
            raise ValueError('An email address is required.')
        email = self.normalize_email(email)
        
        # Security rule: Never auto-verify responder roles during user creation
        extra_fields.setdefault('is_verified_responder', False)

        user = self.model(email=email, role=role, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.ADMIN)
        extra_fields.setdefault('is_verified_responder', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Extensible user model for FixPoint Drive Safe-QR SOS.
    Uses UUID primary key and email for authentication.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255, db_index=True)
    first_name = models.CharField(max_length=64, blank=True)
    last_name = models.CharField(max_length=64, blank=True)
    phone_number = models.CharField(max_length=32, blank=True, db_index=True)
    
    role = models.CharField(
        max_length=32,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER,
        db_index=True
    )
    
    # Responder verification workflow flag:
    # A user selecting POLICE_RESPONDER or MEDICAL_RESPONDER is NOT verified by default.
    is_verified_responder = models.BooleanField(
        default=False,
        help_text="Indicates whether credentials have been verified by system operators/supervisors."
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email
