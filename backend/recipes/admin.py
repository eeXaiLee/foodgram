from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):

    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    ordering = ('id',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):

    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    ordering = ('id',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):

    list_display = ('id', 'name', 'author', 'cooking_time', 'pub_date',)
    list_filter = ('author', 'tags',)
    search_fields = ('name', 'author__email', 'author__username',)
    inlines = (RecipeIngredientInline,)
    ordering = ('-pub_date', 'id',)


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):

    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_filter = ('recipe', 'ingredient',)
    search_fields = ('recipe__name', 'ingredient__name',)
    ordering = ('recipe_id', 'id',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user__email', 'user__username', 'recipe__name',)
    ordering = ('id',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user__email', 'user__username', 'recipe__name',)
    ordering = ('id',)
