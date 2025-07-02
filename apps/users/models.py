from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _
from apps.base.models import BaseModel
from apps.users.managers import (
    RegularManager,
    StaffManager
)
import uuid
from django.utils import timezone
from django.utils.text import slugify

# Create your models here.

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(
        primary_key=True,
        editable=False,
        default=uuid.uuid4,
        verbose_name=_('Id')
    )

    username = models.CharField(
        max_length=32,
        unique=True,
        verbose_name=_('Username')
    )

    slug = models.SlugField(
        max_length=32,
        verbose_name=_('Slug'),
        help_text=_('url-friendly username')
    )

    email = models.EmailField(
        unique=True,
        verbose_name=_('Email')
    )

    password = models.CharField(
        blank=True, # for OAuth signups
        null=True,
        verbose_name=_('Password')
    )

    is_active = models.BooleanField(
        default=True
    )

    is_superuser = models.BooleanField(
        default=False
    )
    
    is_staff = models.BooleanField(
        default=False
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

    regular_objects = RegularManager()
    staff_objects = StaffManager()

    objects = BaseUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def soft_delete(self, *args, **kwargs) -> None:
        """Soft delete with timestamp"""
        self.deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def save(self, *args, **kwargs):
        if not self.slug:  # Only if slug isn't set
            self.slug = slugify(self.username)
        super().save(*args, **kwargs)

    class Meta:
        indexes = [models.Index(fields=['username'])]
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def __str__(self) -> str:
        return f'{self.username}'


class PasswordResetCode(BaseModel):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE
    )

    code = models.CharField(
        max_length=6,
        verbose_name=_('Code')
    )

    class Meta:
        indexes = [models.Index(fields=['code'])]
