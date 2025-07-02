from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.models import BaseModel
from apps.users.models import User
# Create your models here.


class FollowRequest(BaseModel):
    # 'user' requests to follow 'following'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='requests'
    )

    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follow_requests'
    )

    message = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Message')
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Follow Request')
        verbose_name_plural = _('Follow Requests')
        constraints = [
            models.UniqueConstraint(fields=['user', 'following'], name='unique_follow_request')
        ]

    def __str__(self) -> str:
        return f"{self.user.username} requests to follow {self.following.username}"


class Following(BaseModel):
    # 'user' follows 'following'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followings'
    )

    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Followings')
        verbose_name_plural = _('Followings')
        constraints = [
            models.UniqueConstraint(fields=['user', 'following'], name='unique_follow')
        ]

    def __str__(self) -> str:
        return f"{self.user.username} following {self.following.username}"


class Block(BaseModel):
    # 'user' blocks 'blocked'
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blocked_users'
    )

    blocked = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blockers'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Blocks')
        verbose_name_plural = _('Blocks')
        constraints = [
            models.UniqueConstraint(fields=['user', 'blocked'], name='unique_block')
        ]

    def __str__(self) -> str:
        return f"{self.user.username} blocked {self.blocked.username}"
    