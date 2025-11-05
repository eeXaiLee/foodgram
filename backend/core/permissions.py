from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Разрешает чтение всем; запись — только авторизованным авторам.

    При небезопасных методах (POST/PUT/PATCH/DELETE) проверяет, что
    пользователь аутентифицирован, а на уровне объекта — что он автор.

    Args:
        request: Текущий запрос DRF.
        view: Обрабатывающий вью.
        obj: Экземпляр модели (для object-level проверки).

    Returns:
        bool: Разрешён ли доступ.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author_id == getattr(request.user, 'id', None)
