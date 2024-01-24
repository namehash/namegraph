# Load testing

## Install locust

```
pip install locust
```
or using Poetry
```
poetry run pip install locust
```

## Run test

In source file `locust_suggestions_by_category.py` time between requests per user is defined as random number between 1 and 5:
```python
class WebsiteUser(HttpUser):
    wait_time = between(1, 5)
```

Run test with maximum number of 20 users, new user spawning rate 0.1 per second.

```
poetry run locust -f locust_suggestions_by_category.py --users 20 --spawn-rate 0.1 --autostart -t 5m -H "http://54.89.196.85"
```

## Tests

`run_tests.sh` runs load tests with 1 2 3 4 6 8 16 32 parallel users, between time is set to 0.
Tests are made from NameGenerator docker container and logs are saved in `reports` directory.

```commandline
apt update
apt install vim htop
pip3 install locust
cd tests/load_tests
bash run_tests.sh > log 2>&1
```

Memory with number of workers:
- uvicorn 1 5 GB
- uvicorn 2 9 GB
- uvicorn 4 13 GB
- uvicorn 8 31 GB? crash
- gunicorn 4 with preload 8 GB
- gunicorn 8 with preload 11 GB
- r5a.large (2vCPU) gunicorn 8 with preload 11 GB

Conclusions:
- more workers is better, probably more than 2 x vCPU will be better because ES is taking long time
- more workers needs more RAM, we can try more initialization on startup or focus on memory optimization
- with 4 vCPU (4 workers) and 8GB RAM we can serve 934 requests for 4 parallel users in 1 minute with avg time 248 ms (16 req/s)
- with 4 vCPU (8 workers) and 11GB RAM we can serve 1383 requests for 6 parallel users in 1 minute with avg time 247 ms (23 req/s)
- with 2 vCPU (8 workers) and 11GB RAM we can serve 951 requests for 4 parallel users in 1 minute with avg time 243 ms (16 req/s)
- with 2 vCPU (4 workers) and 8GB RAM we can serve 906 requests for 4 parallel users in 1 minute with avg time 255 ms (15 req/s)
- threadpool is better than async for mall number of users
  - 1 user: 335 req/m, avg 177 ms vs 282 req/m, avg 207 ms
  - 32 users: 1146 req/m, avg 1207 ms vs 1277 req/m, avg 1086 ms