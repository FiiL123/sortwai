# sortwai

## Installation

### Prerequisites

- recent versions of Docker with the Compose plugin installed
- Neo4j database (optional)
- Postgres database (optional)

### Set Up

1. Get a copy of the code
```shell
git clone https://github.com/FiiL123/sortwai.git
cd sortwai
```

2. Fill in the environment files
```shell
cp .env.example .env
cp api.env.example api.env
```
- .env file: settings for the `web` container
  + `DEBUG`: When set, detailed error messages will be displayed in case of response errors. Do not use in production.
  + `ALLOWED_HOSTS`: Comma-separated list of host/domain names that the website will serve. This is a security measure.
  + `SECRET_KEY`: In production, must be set to a securely generated random string
  + `DATABASE_URL`: required when using a dedicated postgres database, e. g. `psql://username:password@host/dbname`

- api.env file: settings for comminucation with the LLM
  + `AZURE_OPENAI_ENDPOINT`: the personal endpoint for your LLM resource, without the trailing slash e.g. `https://YOUR_RESOURCE_NAME.openai.azure.com`
  + `AZURE_OPENAI_API_KEY`
  + `AZURE_OPENAI_DEPLOYMENT_NAME`: e.g. `ace-gpt-4o-mini`
  + `OPENAI_API_VERSION`: e. g. `2024-08-01-preview`
  + `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`: required when using a dedicated Neo4j database

3. Run the app
```shell
docker compose up
```

### Maintenance commands
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
