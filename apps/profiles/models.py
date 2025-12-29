import os, uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models import BaseModel
from apps.users.models import User
# Create your models here.

def profile_image_upload(instance, filename) -> str:
    _, extension = os.path.splitext(filename)
    extension = extension.lower()
    return f"profile/{uuid.uuid4()}{extension}"


class Profile(BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
    )

    photo = models.ImageField(
        null=True,
        blank=True,
        upload_to=profile_image_upload,
        verbose_name=_('Photo')
    )

    bio = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Bio')
    )

    # v2.0 features
    is_public = models.BooleanField(
        default=True,
        verbose_name=_('Is public ?')
    )
    
    social_links = models.JSONField(
        default=dict,
        verbose_name=_('Social links')
    )

    location = models.CharField(
        blank=True,
        null=True,
        verbose_name=_('Location')
    )

    views = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Views')
    )
    
    class Meta:
        db_table = 'profiles'
        indexes = [models.Index(fields=['user'])]
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

    def __str__(self) -> str:
        return f"{self.user.username}'s profile"


class ProfilePrivacy(BaseModel):
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name='privacy'
    )
    
    show_email = models.BooleanField(
        default=True,
        verbose_name=_('Show email')
    )

    show_photo = models.BooleanField(
        default=True,
        verbose_name=_('Show photo'),
    )

    show_bio = models.BooleanField(
        default=True,
        verbose_name=_('Show bio'),
    )
    
    show_location = models.BooleanField(
        default=True,
        verbose_name=_('Show location'),
    )

    show_social_links = models.BooleanField(
        default=True,
        verbose_name=_('Show social link'),
    )

    class Meta:
        db_table = 'profile_privacy'
        indexes = [models.Index(fields=['profile'])]
        verbose_name = _('Profile Privacy')
        verbose_name_plural = _('Profiles Privacy')

    def __str__(self) -> str:
        return f"{self.profile.user.username}'s profile privacy"
