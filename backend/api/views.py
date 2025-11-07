from typing import Optional, Type

from django.contrib.auth import get_user_model
from django.db.models import (
    BooleanField,
    Count,
    Exists,
    F,
    OuterRef,
    Sum,
    Value,
)
from django.http import HttpRequest, HttpResponse
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer

from api.filters import IngredientFilter, RecipeFilter
from core.permissions import IsAuthorOrReadOnly
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Subscription

from .serializers import (
    AvatarResponseSerializer,
    FavoriteActionSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    SetAvatarSerializer,
    SetPasswordSerializer,
    ShoppingCartActionSerializer,
    SubscribeActionSerializer,
    SubscriptionUserSerializer,
    TagSerializer,
    UserCreateResponseSerializer,
    UserCreateSerializer,
    UserSerializer,
)

User = get_user_model()


class MultiSerializerViewSetMixin:
    """Выбор сериализатора."""

    serializer_classes: Optional[dict[str, Type[Serializer]]] = None

    def get_serializer_class(self):
        try:
            return self.serializer_classes[self.action]
        except KeyError:
            return super().get_serializer_class()


class ListCreateRetrieveViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Реализация базового вьюсета для list, create и retrieve."""

    pass


class UserViewSet(MultiSerializerViewSetMixin, ListCreateRetrieveViewSet):
    """Реализация работы с пользователями.

    Поддерживает все CRUD операции и дополнительные экшены для
    смены пароля, установки аватара и подписки на других пользователей.
    """

    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    serializer_classes = {
        'create': UserCreateSerializer,
        'set_password': SetPasswordSerializer,
        'subscribe': SubscribeActionSerializer,
        'subscriptions': SubscriptionUserSerializer,
    }

    def create(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        response_serializer = UserCreateResponseSerializer(
            user, context=self.get_serializer_context()
        )
        response_data = response_serializer.data
        headers = self.get_success_headers(response_data)

        return Response(
            response_data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=(IsAuthenticated,),
        url_path='me'
    )
    def me(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=(IsAuthenticated,),
        url_path='set_password'
    )
    def set_password(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=(IsAuthenticated,),
        url_path='me/avatar',
    )
    def me_avatar(self, request, *args, **kwargs) -> Response:
        current_user = request.user

        if request.method == 'DELETE':
            if getattr(current_user, 'avatar', None):
                current_user.avatar.delete(save=False)
                current_user.avatar = ''
                current_user.save(update_fields=['avatar'])
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = SetAvatarSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        url = updated_user.avatar.url
        uri = request.build_absolute_uri(url)
        response_serializer = AvatarResponseSerializer({'avatar': uri})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
        url_path='subscribe',
    )
    def subscribe(self, request: Request, pk: int) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        author = self.get_object()

        data = SubscriptionUserSerializer(
            author, context={'request': request}
        ).data
        return Response(data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request: Request, pk: int) -> Response:
        author = self.get_object()
        deleted, _ = Subscription.objects.filter(
            user=request.user,
            author=author,
        ).delete()
        if deleted == 0:
            return Response(
                {'errors': 'Вы не подписаны.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
    )
    def subscriptions(self, request: Request) -> Response:
        authors = (
            self.get_queryset()
            .filter(subscribers__user=request.user)
            .annotate(recipes_count=Count('recipes'))
        )
        page = self.paginate_queryset(authors)
        serializer = SubscriptionUserSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Реализация работы тегов.

    Выдаёт теги списком и по id без пагинации (стабильный порядок).
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Реализация работы ингредиентов.

    Выдаёт ингредиенты списком и по id без пагинации (стабильный порядок).
    """

    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    queryset = Ingredient.objects.all()
    filterset_class = IngredientFilter


class RecipeViewSet(MultiSerializerViewSetMixin, viewsets.ModelViewSet):
    """Реализация работы с рецептами.

    Поддерживает все CRUD операции и дополнительные экшены для
    добавления/удаления из избранного и корзины, а также выгрузки списка
    покупок.
    """

    queryset = (
        Recipe.objects.select_related('author')
        .prefetch_related('tags', 'recipe_ingredients__ingredient')
    )
    permission_classes = (IsAuthorOrReadOnly,)
    serializer_class = RecipeWriteSerializer
    serializer_classes = {
        'list': RecipeReadSerializer,
        'retrieve': RecipeReadSerializer,
        'favorite': FavoriteActionSerializer,
        'shopping_cart': ShoppingCartActionSerializer,
    }
    filterset_class = RecipeFilter

    @staticmethod
    def _annotate_user_flags(queryset, user):
        """Аннотирует рецепты флагами избранного/корзины для пользователя."""
        if user and user.is_authenticated:
            favorite_subquery = Favorite.objects.filter(
                user=user, recipe=OuterRef('pk')
            )
            cart_subquery = ShoppingCart.objects.filter(
                user=user, recipe=OuterRef('pk')
            )
            return queryset.annotate(
                is_favorited=Exists(favorite_subquery),
                is_in_shopping_cart=Exists(cart_subquery),
            )
        return queryset.annotate(
            is_favorited=Value(False, output_field=BooleanField()),
            is_in_shopping_cart=Value(False, output_field=BooleanField()),
        )

    def get_queryset(self):
        return self._annotate_user_flags(
            super().get_queryset(), self.request.user
        )

    def _recipe_link(
        self,
        request: Request,
        model: type[Favorite] | type[ShoppingCart],
    ) -> Response:
        """Общий обработчик POST/DELETE для избранного и корзины."""
        if request.method == 'POST':
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            recipe = self.get_object()
            data = RecipeShortSerializer(
                recipe, context={'request': request}
            ).data
            return Response(data, status=status.HTTP_201_CREATED)

        recipe = self.get_object()
        deleted, _ = model.objects.filter(
            user=request.user, recipe=recipe
        ).delete()
        if deleted == 0:
            return Response(
                {'errors': 'Нечего удалять.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='favorite',
    )
    def favorite(self, request: Request, pk: int) -> Response:
        """Добавление/удаление рецепта в избранном текущего пользователя."""
        return self._recipe_link(request, Favorite)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
    )
    def shopping_cart(self, request: Request, pk: int) -> Response:
        """Добавление/удаление рецепта в корзине текущего пользователя."""
        return self._recipe_link(request, ShoppingCart)

    def _shopping_rows(self, user):
        """Возвращает queryset с ингредиентами для списка покупок."""
        return (
            RecipeIngredient.objects.filter(
                recipe__in_carts__user=user
            ).values(
                name=F('ingredient__name'),
                unit=F('ingredient__measurement_unit'),
            ).annotate(total=Sum('amount'))
            .order_by('name', 'unit')
        )

    @staticmethod
    def _render_shopping_list(rows) -> str:
        """Форматирует список покупок в текстовый вид."""
        lines = []
        for row in rows:
            lines.append(f'{row["name"]} ({row["unit"]}) — {row["total"]}.')

        if not lines:
            lines = ['Ваш список покупок пуст.']

        return '\n'.join(lines)

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
        url_path='download_shopping_cart',
    )
    def download_shopping_cart(self, request: Request) -> HttpResponse:
        """Выгрузка списка покупок

        Суммирует ингредиенты из корзины текущего пользователя и отдаёт
        .txt файл.
        Формат строки: "Название (ед.) - количество".
        """
        rows = self._shopping_rows(request.user)
        content = self._render_shopping_list(rows)

        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="Shopping_list.txt"'
        )
        return response

    @staticmethod
    def _frontend_recipe_url(request: HttpRequest, recipe_id: int) -> str:
        """Возвращает ссылку на рецепт на фронтенде."""
        base = request.build_absolute_uri('/')[:-1]
        return f'{base}/recipes/{recipe_id}/'

    @action(
        detail=True,
        methods=('get',),
        permission_classes=(AllowAny,),
        url_path='get-link',
    )
    def get_link(self, request: Request, pk: int) -> Response:
        """Получение короткой ссылки на рецепт на фронтенде."""
        recipe = self.get_object()
        short_url = self._frontend_recipe_url(request, recipe.id)
        return Response({'short-link': short_url}, status=status.HTTP_200_OK)
