from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from core.constants import USER_EMAIL_MAX_LEN


class User(AbstractUser):
    """Пользователь системы."""

    email = models.EmailField(
        max_length=USER_EMAIL_MAX_LEN,
        unique=True,
        verbose_name='email'
    )
    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['id']

    def __str__(self) -> str:
        return self.email or self.username


class Subscription(models.Model):
    """Подписка пользователя на автора рецептов."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author',),
                name='unique_subscription_user_author',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_subscription',
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}.'
