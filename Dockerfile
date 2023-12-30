# syntax=docker/dockerfile:1

FROM python:3.10.5-slim-buster as prepare

WORKDIR /app

RUN pip install poetry && \
    poetry config virtualenvs.create false

COPY poetry.lock pyproject.toml ./
RUN poetry install --only main --no-root --no-interaction --no-ansi
RUN poetry export -f requirements.txt -o requirements.txt

ARG AWS_SECRET_ACCESS_KEY
ARG AWS_ACCESS_KEY_ID

COPY data/ data

RUN mkdir generator
COPY generator/download_from_s3.py generator/
COPY conf/ conf
RUN python3 generator/download_from_s3.py


FROM python:3.10.5-slim-buster as app

WORKDIR /app

COPY --from=prepare /app/requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY --from=prepare /app /app

ENV PYTHONPATH=/app

COPY . .
RUN python3 generator/download.py

RUN python3 generator/namehash_common/generate_cache.py

HEALTHCHECK --interval=60s --start-period=60s --retries=3 CMD python3 healthcheck.py

CMD python3 generator/download_names.py && python3 -m uvicorn web_api:app --host 0.0.0.0 --workers 2
