from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import uuid
from apps.base.managers import NonDeletedManager

# Create your models here.
class BaseModel(models.Model):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
        verbose_name=_('Id')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated')
    )

    deleted = models.BooleanField(
        default=False,
        verbose_name=_('Deleted')
    )

    deleted_at = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name=_('Deleted_at')
    )

    objects = models.Manager()
    active_objects = NonDeletedManager()

    def soft_delete(self, *args, **kwargs) -> None:
        """Soft delete with timestamp"""
        self.deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    class Meta:
        abstract = True