from django.conf import settings
from django.core.validators import MinValueValidator
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
        verbose_name_plural = 'Теги'
        ordering = ('id',)

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=128,
        verbose_name='Ингредиент',
    )
    measurement_unit = models.CharField(
        max_length=32,
        verbose_name='Единица измерения',
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('id',)

    def __str__(self) -> str:
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор',
    )
    name = models.CharField(
        max_length=50,
        verbose_name='Название рецепта',
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    image = models.ImageField(
        upload_to='recipes/',
        blank=True,
        null=True,
        verbose_name='Изображение блюда',
    )
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Время готовки (мин)',
        help_text='Минимум 1 минута',
    )
    tags = models.ManyToManyField(
        'recipes.Tag',
        blank=True,
        related_name='recipes',
        verbose_name='Теги',
    )
    Ingredients = models.ManyToManyField(
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
    amount = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Количество',
        help_text='Минимум 1 (единица измерения)',
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


class Favorite(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name='Владелец избранного',
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        related_name='in_favorites',
        verbose_name='Рецепт из избранного',
    )

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

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name='Владелец корзины',
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        related_name='in_carts',
        verbose_name='Рецепт в корзине',
    )

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
