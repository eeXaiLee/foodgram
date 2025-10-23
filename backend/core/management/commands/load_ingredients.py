import csv
import json
from pathlib import Path
from typing import Iterable

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from recipes.models import Ingredient


class Command(BaseCommand):

    help = ('Загрузка ингредиентов.')

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            '--json',
            action='store_true',
            help='Загрузить из data/ingredients.json.'
        )

    def handle(self, *args, **options) -> None:
        data_dir = settings.DATA_DIR
        if not data_dir.exists():
            raise CommandError(f'Директория {data_dir} не найдена.')

        if options.get('json'):
            path = data_dir / 'ingredients.json'
            items = self._read_json(path)
        else:
            path = data_dir / 'ingredients.csv'
            items = self._read_csv(path)

        created = 0
        for item in items:
            name = item.get('name')
            unit = item.get('measurement_unit')
            if not name or not unit:
                self.stderr.write(
                    f'Пропущена запись с данными: {item!r}.'
                )
                continue
            _, is_created = Ingredient.objects.get_or_create(
                name=name,
                measurement_unit=unit,
            )
            created += int(is_created)

        self.stdout.write(
            self.style.SUCCESS(f'Готово. Добавлено {created} ингредиентов.')
        )

    def _read_csv(self, path: Path) -> Iterable[dict]:
        if not path.exists():
            raise CommandError(f'CSV-файл не найден: {path}.')
        with path.open('r', encoding='utf-8') as f:
            data = csv.DictReader(f)
            for row in data:
                yield {
                    'name': row.get('name', '').strip(),
                    'measurement_unit': row.get(
                        'measurement_unit', ''
                    ).strip(),
                }

    def _read_json(self, path: Path) -> Iterable[dict]:
        if not path.exists():
            raise CommandError(f'JSON-файл не найден: {path}.')
        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)
            for row in data:
                yield {
                    'name': str(row.get('name', '')).strip(),
                    'measurement_unit': str(row.get(
                        'measurement_unit', ''
                    )).strip(),
                }
