FROM python:3.12-slim

ARG APP_ENV
RUN echo "BUILDING FOR APP_ENV = ${APP_ENV}"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1


RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

COPY pyproject.toml ./

RUN poetry install --only main --no-ansi --no-root

COPY src ./src
COPY gql_client ./gql_client
COPY graphql ./graphql
COPY gen_graphql_ops.py ./

EXPOSE 8000

CMD ["uvicorn", "src.app_factory:create_app", "--host", "0.0.0.0", "--port", "8888", "--factory"]
