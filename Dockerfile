FROM ghcr.io/trojsten/django-docker:v4 AS web

ENV PYTHONUNBUFFERED 1
ENV PYTHONFAULTHANDLER 1

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get -y upgrade \
    && apt-get -y clean \
    && apt-get install -y curl libzbar0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

USER appuser
COPY --chown=appuser:appuser ./ /app

RUN DATABASE_URL=sqlite://:memory: poetry run ./manage.py collectstatic --no-input
ENV BASE_START=/app/entrypoint.sh

FROM python:3.13-slim-bookworm AS llm-document-api

ENV PYTHONUNBUFFERED 1
ENV PYTHONFAULTHANDLER 1

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get -y upgrade \
    && apt-get -y clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade poetry
RUN useradd -ms /bin/bash appuser
USER appuser

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY --chown=appuser:appuser llm-document-api/main.py ./
COPY --chown=appuser:appuser llm-document-api/text.md ./

CMD ["poetry", "run", "fastapi", "run", "/app/main.py"]
