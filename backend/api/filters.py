from django.db.models import Q
from django_filters import rest_framework as filters

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ['name']

    def filter_name(self, queryset, name, value):
        name_prefix = self.request.query_params.get('name')
        if name_prefix:
            queryset = queryset.filter(name__istartswith=name_prefix)
        return queryset.order_by('name')


class RecipeFilter(filters.FilterSet):
    author = filters.NumberFilter(method='filter_author')
    tags = filters.CharFilter(method='filter_tags')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_author(self, queryset, name, value):
        if value:
            queryset = queryset.filter(author__id=value)
        return queryset

    def filter_tags(self, queryset, name, value):
        tag_params = self.request.query_params.getlist('tags')

        if tag_params:
            slugs = [tag for tag in tag_params if not tag.isdigit()]
            ids = [int(tag) for tag in tag_params if tag.isdigit()]
            queryset = queryset.filter(
                Q(tags__slug__in=slugs) | Q(tags__id__in=ids)
            ).distinct()

        return queryset

    def filter_is_favorited(self, queryset, name, value):
        request_user = (
            self.request.user if self.request.user.is_authenticated else None
        )
        is_favorited = self.request.query_params.get(
            'is_favorited', ''
        ).lower()

        if is_favorited in ('1', 'true'):
            if request_user:
                favorite_ids = Favorite.objects.filter(
                    user=request_user
                ).values_list('recipe_id', flat=True)
                queryset = queryset.filter(id__in=favorite_ids)
            else:
                queryset = queryset.none()

        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        request_user = (
            self.request.user if self.request.user.is_authenticated else None
        )
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart', ''
        ).lower()

        if is_in_shopping_cart in ('1', 'true'):
            if request_user:
                cart_ids = ShoppingCart.objects.filter(
                    user=request_user
                ).values_list('recipe_id', flat=True)
                queryset = queryset.filter(id__in=cart_ids)
            else:
                queryset = queryset.none()

        return queryset
