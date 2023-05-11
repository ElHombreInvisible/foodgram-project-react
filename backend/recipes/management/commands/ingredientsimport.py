import json
from pathlib import Path

from django.core.management.base import BaseCommand

from recipes.models import IngredientModel


class Command(BaseCommand):
    help = 'Импортирует модели ингредиентов из JSON-файла.\n'
    + 'Путь к файлу указывается относительно manage.py,'
    + 'Либо указвается абсолютный путь до файла.'

    def handle(self, *args, **options):
        if not options['path']:
            print('Укажите путь до файла в формате "-p <Путь_к_файлу>"')
            return
        path = Path(options['path'])
        if not path.exists():
            print('Указан неверный путь к файлу')
            return
        if path.suffix != '.json':
            print(f'Предупреждение: файл {path} имеет некорректное ' +
                  'расширение.\nПродолжить? [Y/n]')
            answer = input().lower()
            while answer not in ('y', 'n'):
                print('Некорректный ответ.\nПродолжить? [Y/n]')
                answer = input().lower()
            if answer == 'n':
                print('Выполнение прервано.')
                return
        with open(path, mode='r', encoding='utf-8') as file:
            data = json.load(file)
        count = IngredientModel.objects.all().count()
        for ingredient in data:
            try:
                IngredientModel.objects.get_or_create(**ingredient)
            except Exception:
                print('Произошла ошибка при добавлении ингредиента:',
                      ingredient)
                continue
        new = IngredientModel.objects.all().count() - count
        print(f'Было добавлено {new} ингредиентов.')

    def add_arguments(self, parser):
        parser.add_argument('-p', '--path', action='store')
        return super().add_arguments(parser)
