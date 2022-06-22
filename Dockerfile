# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN pip3 install --no-cache-dir -e .

RUN python3 generator/download.py

CMD python3 generator/download_names.py && python3 -m uvicorn web_api:app --host 0.0.0.0