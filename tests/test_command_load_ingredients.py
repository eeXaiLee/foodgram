import csv

import pytest
from django.core.management import call_command

from recipes.models import Ingredient


@pytest.mark.django_db
def test_load_ingredients(settings, tmp_path, capsys):
    data_dir = tmp_path / 'data'
    data_dir.mkdir()

    csv_path = data_dir / 'ingredients.csv'
    with csv_path.open('w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['name', 'measurement_unit'])
        writer.writerow(['Сахар', 'г'])
        writer.writerow(['Соль', 'г'])

    settings.DATA_DIR = data_dir

    call_command('load_ingredients')

    ingredients = set(Ingredient.objects.values_list('name', flat=True))
    assert {'Сахар', 'Соль'}.issubset(ingredients)

    out = capsys.readouterr().out
    assert 'Добавлено' in out
