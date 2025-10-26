import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()


@pytest.fixture(autouse=True)
def _enable_db(db):
    pass


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='user1@example.com',
        username='user1',
        password='password1',
        first_name='User',
        last_name='One',
    )


@pytest.fixture
def another_user(db):
    return User.objects.create_user(
        email='user2@example.com',
        username='user2',
        password='password2',
        first_name='User',
        last_name='Two',
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def tag(db):
    return Tag.objects.create(name='Завтрак', slug='breakfast')


@pytest.fixture
def ingredient(db):
    return Ingredient.objects.create(name='Яйцо', measurement_unit='шт')


@pytest.fixture
def make_recipe(user, tag, ingredient):
    def _make_recipe(name='Омлет', amount=2):
        recipe = Recipe.objects.create(
            author=user,
            name=name,
            text='Домашний омлет',
            cooking_time=10,
        )

        recipe.tags.add(tag)

        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=ingredient,
            amount=amount,
        )

        return recipe
    return _make_recipe
