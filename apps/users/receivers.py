from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from apps.users.models import User


@receiver(pre_save, sender=User)
def user_pre_save(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = slugify(instance.username)