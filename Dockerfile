# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

COPY . .

RUN pip3 install -e .

RUN python3 generator/download.py

CMD [ "python3", "-m" , "uvicorn", "web_api:app", "--reload"]