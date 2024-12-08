# sortwai

## how-to
Run the app
```shell
docker compose up 
```
Make migrations
```shell
docker compose run --rm web poetry run python manage.py makemigrations 
```
Migrate
```shell
docker compose run --rm web poetry run python manage.py migrate 
```
Load dummy data
```shell
docker compose run --rm web poetry run python manage.py loaddata dummy_data.json
```
