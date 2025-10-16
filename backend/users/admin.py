from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):

    list_display = (
        'id', 'email', 'username', 'first_name', 'last_name', 'is_staff'
    )
    list_display_links = ('id', 'email')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('id',)

    fieldsets = (
        ('Учётная запись', {'fields': ('email', 'username', 'password')}),
        ('Личная информация', {
            'fields': ('first_name', 'last_name', 'avatar')
        }),
        ('Права доступа', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'first_name',
                'last_name',
                'password1',
                'password2'
            )
        }),
    )
