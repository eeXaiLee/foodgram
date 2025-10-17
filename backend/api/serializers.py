import base64
import uuid
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from rest_framework import serializers

from recipes.models import Tag

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):

    is_subscribed = serializers.BooleanField(read_only=True, default=False)
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
        return str(request.build_absolute_uri(url)) if request else str(url)


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
        content_file = ContentFile(image_bytes, name=unique_name)
        return content_file

    def save(self, *args, **kwargs) -> AbstractUser:
        user = self.context['request'].user
        content_file = self._decode_base64(self.validated_data['avatar'])
        user.avatar.save(content_file.name, content_file, save=True)
        return user


class AvatarResponseSerializer(serializers.Serializer):
    avatar = serializers.CharField()


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug',)
        read_only_fields = ('id', 'name', 'slug',)
