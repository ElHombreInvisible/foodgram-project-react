# Foodgram project
### Кулинарный помощник с рецептами
Представляет из себя веб-сервис с регистрацией, на котором можно найти рецепты, а также добавить свои, держать список избранных рецептов и авторов, получить список покупок для желаемых рецептов
# Установка
## Инструкции по запуску:
- установить Docker
- склонировать проект ```git clone <project_link>```
- настроить .env-файл
- выполнить команду ```docker-compose up```
- применить миграции ```docker-compose exec web python manage.py migrate```
- создать суперпользователя командой ```docker-compose exec web python manage.py createsuperuser```
- собрать файлы статики для сервера nginx ```docker-compose exec web python manage.py collectstatic --no-input```
# Для переноса базы данных:
- выполнить команду для дампа текущей базы данных```docker-compose exec web python manage.py dumpdata > fixtures.json```
- заполнить базу данных из дампа командой ```docker-compose exec web python manage.py loaddata fixtures.json```
# Загрузка таблицы ингредиентов:
c помощью manage-команды заполнить таблицу ингредиентов ```docker-compose exec web python manage.py ingredientsimport -p <Путь_к_файлу>(заготовленные фикстуры ингредиентов - в import/ingredients.json)```