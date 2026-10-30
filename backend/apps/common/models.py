import uuid
from django.db import models

class TimeStampedModel(models.Model):
    """
    Abstract base model providing self-updating created_at and updated_at fields.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

class UUIDModel(models.Model):
    """
    Abstract base model providing a UUID primary key.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True

class BaseModel(UUIDModel, TimeStampedModel):
    """
    Combined abstract base model with UUID primary key and timestamp tracking.
    """
    class Meta:
        abstract = True
        ordering = ['-created_at']
