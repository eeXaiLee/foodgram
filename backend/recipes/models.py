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


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Ингредиент'
    )
    measurement_unit = models.CharField(
        max_length=32,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['id',]

    def __str__(self) -> str:
        return f'{self.name} ({self.measurement_unit})'
