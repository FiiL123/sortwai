FROM python:3.13-slim-bookworm AS web

ENV PYTHONUNBUFFERED 1
ENV PYTHONFAULTHANDLER 1

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get -y upgrade \
    && apt-get -y clean \
    && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade poetry
RUN useradd -ms /bin/bash appuser
USER appuser

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

COPY --chown=appuser:appuser ./ /app

RUN DATABASE_URL=sqlite://:memory: poetry run ./manage.py collectstatic --no-input
ENV BASE_START=/app/entrypoint.sh
