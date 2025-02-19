# syntax=docker/dockerfile:1

FROM python:3.11.7-slim-bookworm as prepare

WORKDIR /app

RUN pip install poetry && \
    poetry config virtualenvs.create false

RUN apt-get update && \
    apt-get install -y gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY poetry.lock pyproject.toml ./
RUN poetry install --only main --no-root --no-interaction --no-ansi
RUN poetry self add poetry-plugin-export
RUN poetry export -f requirements.txt -o requirements.txt

COPY data/ data

RUN mkdir namegraph
COPY namegraph/download_from_s3.py namegraph/
COPY conf/ conf
RUN python3 namegraph/download_from_s3.py


FROM python:3.11.7-slim-bookworm as app

WORKDIR /app

RUN apt-get update && \
    apt-get install -y gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=prepare /app/requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY --from=prepare /app /app

ENV PYTHONPATH=/app

COPY . .
RUN python3 namegraph/download.py

RUN python3 namegraph/namehash_common/generate_cache.py

HEALTHCHECK --interval=60s --start-period=60s --retries=3 CMD python3 healthcheck.py

CMD python3 namegraph/download_names.py && gunicorn web_api:app --bind 0.0.0.0 --workers 2 --timeout 120 --preload --worker-class uvicorn.workers.UvicornWorker
