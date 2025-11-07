import base64
import uuid
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
)
from rest_framework import serializers

from core.constants import (
    MAX_COOKING_TIME,
    MAX_INGREDIENT_AMOUNT,
    MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT,
)
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


def _decode_base64(data: str) -> ContentFile:
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
    """Строит URL.

    Строит абсолютный URL, если есть request; иначе возвращает url.
    """
    return str(request.build_absolute_uri(url)) if request else str(url)


def _current_user(context: dict) -> AbstractUser:
    """Возвращает текущего аутентифицированного пользователя."""
    request = context.get('request')
    return getattr(request, 'user', None)


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор пользователя."""

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


class UserCreateSerializer(DjoserUserCreateSerializer):
    """Создание пользователя."""

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    class Meta(DjoserUserCreateSerializer.Meta):
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
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def create(self, validated_data: dict) -> AbstractUser:
        return User.objects.create_user(**validated_data)


class UserCreateResponseSerializer(serializers.ModelSerializer):
    """Ответ при создании пользователя."""

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
    """Смена пароля пользователя."""

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
    """Установка аватара пользователя."""

    avatar = serializers.CharField(write_only=True)

    def save(self, *args, **kwargs) -> AbstractUser:
        user = self.context['request'].user
        content_file = _decode_base64(self.validated_data['avatar'])
        user.avatar.save(content_file.name, content_file, save=True)
        return user


class AvatarResponseSerializer(serializers.Serializer):
    """Ответ с аватаром пользователя."""

    avatar = serializers.CharField()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тега."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)
        read_only_fields = ('id', 'name', 'slug',)


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиента."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientInSerializer(serializers.Serializer):
    """Ингредиент в рецепте при создании/обновлении."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        min_value=MIN_INGREDIENT_AMOUNT,
        max_value=MAX_INGREDIENT_AMOUNT,
    )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Ингредиент в рецепте при чтении."""

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
    """Рецепт при чтении."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='recipe_ingredients',
        read_only=True,
    )
    image = serializers.SerializerMethodField()
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

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

    def get_image(self, obj: Recipe) -> str:
        request = self.context.get('request')
        return _absolute_url(request, obj.image.url)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Рецепт при создании/обновлении."""

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

    def validate(self, attrs: dict) -> dict:
        cooking_time = attrs.get('cooking_time')
        if cooking_time is not None:
            if cooking_time < MIN_COOKING_TIME:
                raise serializers.ValidationError(
                    f'Время готовки не может быть меньше {MIN_COOKING_TIME} '
                    'минуты.'
                )
            if cooking_time > MAX_COOKING_TIME:
                raise serializers.ValidationError(
                    f'Время готовки не может быть больше {MAX_COOKING_TIME} '
                    'минут.'
                )
        return attrs

    def validate_ingredients(self, value: list[dict[str, Any]]):
        if not value:
            raise serializers.ValidationError(
                f'Нужен хотя бы {MIN_INGREDIENT_AMOUNT} ингредиент.'
            )
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

    @staticmethod
    def _assign_image(instance: Recipe, image_b64: str) -> None:
        """Декодирует base64 и сохраняет изображение в instance.image."""
        content = _decode_base64(image_b64)
        instance.image.save(content.name, content, save=False)

    def _apply_tags_ingredients(
        self,
        instance: Recipe,
        tags: list[Tag],
        ingredients: list[dict[str, Any]],
    ) -> None:
        """Применяет теги и ингредиенты к рецепту."""
        instance.tags.set(tags)

        RecipeIngredient.objects.filter(recipe=instance).delete()
        self._set_ingredients(instance, ingredients)

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> Recipe:
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        image_b64 = validated_data.pop('image')
        recipe = Recipe(
            author=self.context['request'].user,
            **validated_data,
        )
        self._assign_image(recipe, image_b64)
        recipe.save()

        self._apply_tags_ingredients(recipe, tags, ingredients)

        return recipe

    @transaction.atomic
    def update(
        self, instance: Recipe, validated_data: dict[str, Any]
    ) -> Recipe:
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        image_b64 = validated_data.pop('image', None)

        instance = super().update(instance, validated_data)

        if image_b64 is not None:
            self._assign_image(instance, image_b64)
            instance.save(update_fields=['image'])

        self._apply_tags_ingredients(instance, tags, ingredients)

        return instance

    def to_representation(self, instance: Recipe) -> dict[str, Any]:
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Краткий рецепт."""

    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')

    def get_image(self, obj: Recipe) -> str:
        request = self.context.get('request')
        return _absolute_url(request, obj.image.url)


class SubscriptionUserSerializer(UserSerializer):
    """Пользователь с подписками."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True, default=0)

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
        limit = None
        if isinstance(raw_limit, str) and raw_limit.isdigit():
            limit = int(raw_limit)

        queryset = Recipe.objects.filter(author=obj)
        if limit:
            queryset = queryset[:limit]

        return RecipeShortSerializer(
            queryset, many=True, context=self.context
        ).data


class SubscribeActionSerializer(serializers.Serializer):
    """Валидация действий подписки."""

    def validate(self, attrs):
        request = self.context['request']
        view = self.context['view']
        author = view.get_object()
        user = request.user

        if author == user:
            raise serializers.ValidationError(
                {'errors': 'Нельзя подписаться на себя.'}
            )
        if Subscription.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                {'errors': 'Уже подписаны.'}
            )
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        author = self.context['view'].get_object()
        return Subscription.objects.create(user=request.user, author=author)


class FavoriteActionSerializer(serializers.Serializer):
    """Валидация действий избранного."""

    def validate(self, attrs):
        request = self.context['request']
        view = self.context['view']
        recipe = view.get_object()
        user = request.user

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                {'errors': 'Рецепт уже в избранном.'}
            )
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        recipe = self.context['view'].get_object()
        return Favorite.objects.create(user=request.user, recipe=recipe)


class ShoppingCartActionSerializer(serializers.Serializer):
    """Валидация действий корзины покупок."""

    def validate(self, attrs):
        request = self.context['request']
        view = self.context['view']
        recipe = view.get_object()
        user = request.user

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                {'errors': 'Рецепт уже в корзине покупок.'}
            )
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        recipe = self.context['view'].get_object()
        return ShoppingCart.objects.create(user=request.user, recipe=recipe)
