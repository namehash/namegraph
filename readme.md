# Install

```
pip3 install -e .
```

# Usage

The application can be run:
* reading queries from stdin
* reading query as an argument

The first run will download additional resources (e.g. dictionaries).

## Queries from stdin

```
python ./generator/app.py app.input=stdin
```

## Query as an argument

The application can be run with

```
python ./generator/app.py
```

It will generate suggestions for the default query.

The default parameters are defined in `conf/config.yaml`. Any of the parameters might be substituted with a path to the
parameter, with dot-separated fragments, e.g.

```
python ./generator/app.py app.query=firepower
```

will substitute the default query with the provided one.

The parameters are documented in the config.

# REST API

Start server:
```
python -m uvicorn web_api:app --reload
```

Query with POST:
```
curl -d '{"name":"fire"}' -H "Content-Type: application/json" -X POST http://localhost:8000
```

# Tests

Run:
```
pytest
```
or without slow tests:
```
pytest -m "not slow"
```

## Debugging

Run app with `app.logging_level=DEBUG` to see debug information:
```
python generator/app.py app.input=stdin app.logging_level=DEBUG
```

# Deployment

## Build Docker image locally

Set image TAG:

`export TAG=0.1.0

Build a Docker image locally

`docker compose -f docker-compose.build.yml build`

Authorize to Amazon:

aws-conf xxxxxx (MFA code)

Authorize to ECR:

`./authorize-ecr.sh`

Push image to ECR:

`docker push 571094861812.dkr.ecr.us-east-1.amazonaws.com/name-generator:${TAG}

## Deploy image on remote instance

Authorize EC2 instance in ECR:

`aws ecr get-login-password | docker login --username AWS --password-stdin 571094861812.dkr.ecr.us-east-1.amazonaws.com/name-generator`

(Re-Deploy) image:

`docker compose up -d`
