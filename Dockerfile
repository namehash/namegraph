# syntax=docker/dockerfile:1

FROM python:3.10.5-slim-buster as prepare

ARG AWS_SECRET_ACCESS_KEY
ARG AWS_ACCESS_KEY_ID

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

COPY data/ data

RUN mkdir generator
COPY generator/download_from_s3.py generator/
COPY conf/ conf
RUN python3 generator/download_from_s3.py 


FROM python:3.10.5-slim-buster as app

COPY --from=prepare /app /app
WORKDIR /app
COPY setup.py .
RUN pip3 install --no-cache-dir -e .

COPY . .
RUN python3 generator/download.py

HEALTHCHECK --interval=60s --start-period=60s --retries=3 CMD python3 healthcheck.py

CMD python3 generator/download_names.py && python3 -m uvicorn web_api:app --host 0.0.0.0
