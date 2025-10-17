from django.db import models


class Tag(models.Model):

    name = models.CharField(
        max_length=32,
        unique=True,
        verbose_name='Тег',
    )
    slug = models.SlugField(
        max_length=32,
        unique=True,
        verbose_name='Слаг',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги',
        ordering = ['id',]

    def __str__(self) -> str:
        return self.name
