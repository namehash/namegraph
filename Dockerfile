# syntax=docker/dockerfile:1

FROM python:3.10.5-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

RUN mkdir generator
COPY generator/download*.py generator/
COPY conf/ .
RUN python3 generator/download.py

COPY . .

RUN pip3 install --no-cache-dir -e .

CMD python3 generator/download_names.py && python3 -m uvicorn web_api:app --host 0.0.0.0