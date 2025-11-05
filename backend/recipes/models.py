from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.constants import (
    INGREDIENT_MEASUREMENT_UNIT_MAX_LEN,
    INGREDIENT_NAME_MAX_LEN,
    MAX_COOKING_TIME,
    MAX_INGREDIENT_AMOUNT,
    MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT,
    RECIPE_NAME_MAX_LEN,
    TAG_NAME_MAX_LEN,
    TAG_SLUG_MAX_LEN,
)


class Tag(models.Model):
    """Тег рецепта."""

    name = models.CharField(
        max_length=TAG_NAME_MAX_LEN,
        unique=True,
        verbose_name='Тег',
    )
    slug = models.SlugField(
        max_length=TAG_SLUG_MAX_LEN,
        blank=True,
        null=True,
        unique=True,
        verbose_name='Слаг',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('id',)

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Ингредиент рецепта."""

    name = models.CharField(
        max_length=INGREDIENT_NAME_MAX_LEN,
        unique=True,
        verbose_name='Ингредиент',
    )
    measurement_unit = models.CharField(
        max_length=INGREDIENT_MEASUREMENT_UNIT_MAX_LEN,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('id',)

    def __str__(self) -> str:
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Рецепт."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=RECIPE_NAME_MAX_LEN,
        verbose_name='Название рецепта',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    image = models.ImageField(
        upload_to='recipes/',
        verbose_name='Изображение блюда',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME),
        ],
        verbose_name='Время готовки (мин)',
        help_text='От 1 до 1440 минут.',
    )
    tags = models.ManyToManyField(
        'recipes.Tag',
        blank=True,
        related_name='recipes',
        verbose_name='Теги',
    )
    ingredients = models.ManyToManyField(
        'recipes.Ingredient',
        through='recipes.RecipeIngredient',
        related_name='recipes',
        verbose_name='Ингредиенты',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date', 'id',)
        constraints = [
            models.UniqueConstraint(
                fields=('author', 'name'),
                name='unique_recipe_name_per_author',
            )
        ]

    def __str__(self):
        return f'{self.name} - {self.author}'


class RecipeIngredient(models.Model):
    """Ингредиент в рецепте с указанием количества."""

    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Связанный рецепт',
    )
    ingredient = models.ForeignKey(
        'recipes.Ingredient',
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipes',
        verbose_name='Связанный ингредиент',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_INGREDIENT_AMOUNT),
            MaxValueValidator(MAX_INGREDIENT_AMOUNT),
        ],
        verbose_name='Количество',
        help_text='От 1 до 10000 (единица измерения).',
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'
        ordering = ('recipe_id', 'id',)
        constraints = [
            models.UniqueConstraint(
                fields=('recipe', 'ingredient'),
                name='unique_ingredient_per_recipe',
            )
        ]

    def __str__(self):
        return f'{self.ingredient} x {self.amount}'


class UserRecipeListBase(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True


class Favorite(UserRecipeListBase):
    """Избранное пользователя."""

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite_user_recipe',
            )
        ]

    def __str__(self):
        return f'{self.user} ✯ {self.recipe}'


class ShoppingCart(models.Model):
    """Корзина покупок пользователя."""

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_cart_user_recipe',
            )
        ]

    def __str__(self):
        return f'{self.recipe} в корзине пользователя {self.user}'
