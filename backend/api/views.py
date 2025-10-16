from typing import Type

from django.contrib.auth import get_user_model
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import (
    AvatarResponseSerializer,
    SetAvatarSerializer,
    SetPasswordSerializer,
    UserCreateResponseSerializer,
    UserCreateSerializer,
    UserSerializer,
)

User = get_user_model()


class UserViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):

    queryset = User.objects.all().order_by('id')
    permission_classes = (permissions.AllowAny,)

    def get_serializer_class(self) -> (
            Type[UserCreateSerializer | SetPasswordSerializer | UserSerializer]
    ):
        if self.action == 'create':
            return UserCreateSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return UserSerializer

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
        permission_classes=[permissions.IsAuthenticated],
        url_path='me'
    )
    def me(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated],
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
        permission_classes=[permissions.IsAuthenticated],
        url_path='me/avatar',
    )
    def me_avatar(self, request, *args, **kwargs) -> Response:
        current_user = request.user

        if request.method == 'DELETE':
            if getattr(current_user, 'avatar', None):
                current_user.avatar.delete(save=False)
                current_user.avatar = None
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
