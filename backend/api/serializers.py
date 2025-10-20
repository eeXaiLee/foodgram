import base64
import uuid
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from django.db import transaction
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription

User = get_user_model()


def _decode_base64(self, data: str) -> ContentFile:
    """Превращает base64-строку в ContentFile с расширением."""
    if data.startswith('data:') and ';base64,' in data:
        data_uri_header, base64_string = data.split(';base64,', 1)
        file_extension = (
            data_uri_header.split('/')[-1]
            if '/' in data_uri_header
            else 'png'
        )
    else:
        base64_string = data
        file_extension = 'png'

    image_bytes = base64.b64decode(base64_string)
    unique_name = f'{uuid.uuid4()}.{file_extension}'
    return ContentFile(image_bytes, name=unique_name)


def _absolute_url(request, url: str) -> str:
    """
    Строит URL.

    Строит абсолютный URL, если есть request; иначе возвращает url.
    """
    return str(request.build_absolute_uri(url)) if request else str(url)


def _current_user(context: dict) -> AbstractUser:
    """Возвращает текущего аутентифицированного пользователя."""
    request = context.get('request')
    return getattr(request, 'user', None)


class UserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        read_only_fields = ('id', 'is_subscribed', 'avatar')

    def get_avatar(self, obj: Any) -> str | None:
        if not getattr(obj, "avatar", None):
            return None
        request = self.context.get('request')
        url = obj.avatar.url
        return _absolute_url(request, url)

    def get_is_subscribed(self, obj: Any) -> bool:
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        return Subscription.objects.filter(user=user, author=obj).exists()


class UserCreateSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        read_only_fields = ('id',)

    def create(self, validated_data: dict) -> AbstractUser:
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserCreateResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
        )
        read_only_fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
        )


class SetPasswordSerializer(serializers.Serializer):

    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )
    current_password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        user = self.context['request'].user
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError(
                {'current_password': ['Неверный пароль.']}
            )
        return attrs

    def save(self, **kwargs) -> AbstractUser:
        user = self.context['request'].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=['password'])
        return user


class SetAvatarSerializer(serializers.Serializer):
    avatar = serializers.CharField(write_only=True)

    def save(self, *args, **kwargs) -> AbstractUser:
        user = self.context['request'].user
        content_file = _decode_base64(self.validated_data['avatar'])
        user.avatar.save(content_file.name, content_file, save=True)
        return user


class AvatarResponseSerializer(serializers.Serializer):
    avatar = serializers.CharField()


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)
        read_only_fields = ('id', 'name', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientInSerializer(serializers.Serializer):

    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class IngredientInRecipeSerializer(serializers.ModelSerializer):

    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount',)
        read_only_fields = ('id', 'name', 'measurement_unit', 'amount',)


class RecipeReadSerializer(serializers.ModelSerializer):

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='recipe_ingredients',
        read_only=True,
    )
    image = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'text',
            'image',
            'cooking_time',
            'tags',
            'ingredients',
            'pub_date',
            'is_favorited',
            'is_in_shopping_cart',
        )
        read_only_fields = (
            'id',
            'author',
            'name',
            'text',
            'image',
            'cooking_time',
            'tags',
            'ingredients',
            'pub_date',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_image(self, obj: Recipe) -> str | None:
        if not obj.image:
            return None
        request = self.context.get('request')
        return _absolute_url(request, obj.image.url)

    def get_is_favorited(self, obj: Recipe) -> bool:
        user = self._current_user(self.context)
        if not user or not user.is_authenticated:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj: Recipe) -> bool:
        user = self._current_user(self.context)
        if not user or not user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):

    ingredients = RecipeIngredientInSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
    )
    image = serializers.CharField(required=True)

    class Meta:
        model = Recipe
        fields = (
            'name',
            'text',
            'image',
            'cooking_time',
            'tags',
            'ingredients',
        )

    def validate_ingredients(self, value: list[dict[str, Any]]):
        if not value:
            raise serializers.ValidationError('Нужен хотя бы 1 ингредиент.')
        ids = [item['id'] for item in value]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                'Ингредиенты должны быть уникальны.'
            )
        existing = set(
            Ingredient.objects.filter(id__in=ids).values_list('id', flat=True)
        )
        missing = [id for id in ids if id not in existing]
        if missing:
            raise serializers.ValidationError(f'Нет ингредиентов: {missing}.')
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Нужен хотя бы 1 тег.')
        return value

    def _set_ingredients(
            self, recipe: Recipe, items: list[dict[str, Any]]
    ) -> None:
        links = []
        for item in items:
            links.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient_id=item['id'],
                    amount=item['amount'],
                )
            )
        RecipeIngredient.objects.bulk_create(links)

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> Recipe:
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        image_b64 = validated_data.pop('image')
        recipe = Recipe(
            author=self.context['request'].user,
            **validated_data,
        )
        content = _decode_base64(image_b64)
        recipe.image.save(content.name, content, save=False)
        recipe.save()

        recipe.tags.set(tags)
        self._set_ingredients(recipe, ingredients)

        return recipe

    @transaction.atomic
    def update(
        self, instance: Recipe, validated_data: dict[str, Any]
    ) -> Recipe:
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)
        image_b64 = validated_data.pop('image', None)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)

        if image_b64 is not None:
            if image_b64:
                content = _decode_base64(image_b64)
                instance.image.save(content.name, content, save=False)
            else:
                if instance.image:
                    instance.image.delete(save=False)
                instance.image = None
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        if ingredients is not None:
            RecipeIngredient.objects.filter(recipe=instance).delete()
            self._set_ingredients(instance, ingredients)

        return instance

    def to_representation(self, instance: Recipe) -> dict[str, Any]:
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):

    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj: Recipe) -> str | None:
        if not obj.image:
            return None
        request = self.context.get('request')
        return _absolute_url(request, obj.image.url)


class SubscriptionUserSerializer(UserSerializer):

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')
        read_only_fields = UserSerializer.Meta.read_only_fields + (
            'recipes', 'recipes_count'
        )

    def get_is_subscribed(self, obj: Any) -> bool:
        return True

    def get_recipes(self, obj: Any) -> list[dict]:
        request = self.context.get('request')
        raw_limit = (
            request.query_params.get('recipes_limit') if request else None
        )
        try:
            limit = int(raw_limit) if raw_limit else None
        except (TypeError, ValueError):
            limit = None

        queryset = (
            Recipe.objects.filter(author=obj).order_by('-pub_date', 'id')
        )
        if limit:
            queryset = queryset[:limit]

        return RecipeShortSerializer(
            queryset, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj: Any) -> int:
        return Recipe.objects.filter(author=obj).count()
