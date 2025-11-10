from django.contrib import admin
from django.db.models import Prefetch

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
    list_display_links = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('id',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):

    list_display = ('id', 'name', 'measurement_unit')
    list_display_links = ('name',)
    search_fields = ('name',)
    ordering = ('id',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    autocomplete_fields = ('ingredient',)
    fields = ('ingredient', 'amount',)
    show_change_link = True
    extra = 1
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):

    list_display = (
        'id', 'name', 'author', 'cooking_time', 'pub_date', 'favorites_count',
    )
    list_display_links = ('name', 'author')
    list_filter = ('author', 'tags',)
    filter_horizontal = ('tags',)
    search_fields = ('name', 'author__email', 'author__username',)
    inlines = (RecipeIngredientInline,)
    list_select_related = ('author',)
    readonly_fields = ('favorites_count',)
    ordering = ('-pub_date', 'id',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('author').prefetch_related(
            'tags',
            Prefetch('recipe_ingredients',
                     queryset=RecipeIngredient.objects.select_related(
                         'ingredient'
                     )),
        )

    def favorites_count(self, obj):
        return Favorite.objects.filter(recipe=obj).count()

    favorites_count.short_description = 'В избранном'


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):

    list_display = ('id', 'recipe', 'ingredient', 'amount')
    list_display_links = ('recipe', 'ingredient')
    list_filter = ('recipe', 'ingredient',)
    search_fields = ('recipe__name', 'ingredient__name',)
    raw_id_fields = ('recipe', 'ingredient',)
    ordering = ('recipe_id', 'id',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('recipe', 'ingredient')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'recipe')
    list_display_links = ('user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user__email', 'user__username', 'recipe__name',)
    list_select_related = ('user', 'recipe',)
    raw_id_fields = ('user', 'recipe',)
    ordering = ('id',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'recipe', 'recipe__author')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):

    list_display = ('id', 'user', 'recipe')
    list_display_links = ('user', 'recipe')
    list_filter = ('user',)
    search_fields = ('user__email', 'user__username', 'recipe__name',)
    list_select_related = ('user', 'recipe',)
    raw_id_fields = ('user', 'recipe',)
    ordering = ('id',)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'recipe', 'recipe__author')
