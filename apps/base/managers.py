from django.db import models

class NonDeletedManager(models.Manager):
    """Manager that returns only non-deleted objects"""
    def get_queryset(self):
        return super().get_queryset().filter(deleted=False)